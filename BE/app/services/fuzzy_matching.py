"""
DyLeks Dyslexia-Aware Fuzzy Matching Engine.

Alasan ('Why'):
  OCR biasa (TrOCR) hanya membaca "apa yang tertulis" dan membandingkannya
  secara string sederhana. Ini TIDAK cukup untuk diagnosis pedagogis disleksia
  karena:

  1. Anak disleksia memiliki pola kesalahan yang SPESIFIK dan BERULANG,
     bukan sekadar "typo acak". Pola ini adalah sinyal klinis, bukan noise.
  2. Fuzzy matching standar (Levenshtein) menganggap b->d sama besarnya
     dengan a->z. Padahal b/d adalah inversi visual khas disleksia yang
     harus diberi bobot risiko LEBIH TINGGI.
  3. Bahasa Indonesia memiliki digraf (NG, NY, KH, SY) dan diftong (AI, AU, OI)
     yang harus diperlakukan sebagai satu unit fonetik, bukan dua karakter terpisah.

Modul ini mengimplementasikan:
  - DyslexiaFuzzyMatcher: Kelas utama dengan scoring yang peka terhadap
    pola kesalahan khas disleksia (Indonesian-language aware).
  - MatchResult: Dataclass terstruktur agar output mudah dikonsumsi
    oleh scoring_service.py dan frontend.
"""

from dataclasses import dataclass, field
from typing import Optional
from rapidfuzz import fuzz, distance


# ============================================================
# KONFIGURASI LINGUISTIK BAHASA INDONESIA
# ============================================================

# Pasangan huruf yang SECARA VISUAL mudah tertukar oleh anak disleksia.
# Kunci = huruf target, Nilai = huruf yang kemungkinan besar salah ditulis.
# Bobot lebih tinggi = kesalahan lebih signifikan secara klinis.
DYSLEXIA_REVERSAL_PAIRS: dict[tuple[str, str], float] = {
    # Inversi Vertikal (paling umum, ciri utama disleksia)
    ("b", "d"): 1.8,
    ("d", "b"): 1.8,
    ("p", "q"): 1.8,
    ("q", "p"): 1.8,
    # Inversi Horizontal
    ("b", "p"): 1.4,
    ("p", "b"): 1.4,
    ("d", "q"): 1.4,
    ("q", "d"): 1.4,
    # Inversi Angka (juga sering terjadi)
    ("6", "9"): 1.5,
    ("9", "6"): 1.5,
    # Pasangan visual lain yang sering dilaporkan
    ("n", "u"): 1.2,
    ("u", "n"): 1.2,
    ("m", "w"): 1.3,
    ("w", "m"): 1.3,
    ("f", "t"): 1.1,
}

# Digraf Bahasa Indonesia yang harus diperlakukan sebagai satu unit fonetik.
# Ini penting agar "NG" tidak dihitung sebagai 2 penghapusan terpisah.
INDONESIAN_DIGRAPHS = ["ng", "ny", "kh", "sy"]

# Diftong Bahasa Indonesia
INDONESIAN_DIPHTHONGS = ["ai", "au", "oi"]


# ============================================================
# DATACLASS OUTPUT
# ============================================================

@dataclass
class ErrorDetail:
    """Representasi satu instance kesalahan spesifik yang terdeteksi."""
    error_type: str          # reversal | omission | insertion | substitution | transposition
    target_char: str         # Karakter yang seharusnya ditulis
    detected_char: str       # Karakter yang terdeteksi OCR
    position: int            # Indeks posisi dalam kata
    severity: str            # low | medium | high | critical
    description: str         # Pesan deskriptif untuk guru


@dataclass
class MatchResult:
    """
    Hasil lengkap analisis satu kata dari mesin fuzzy matching DyLeks.
    Didesain agar langsung bisa dikonsumsi oleh scoring_service dan frontend.
    """
    target_word: str
    detected_word: str
    is_correct: bool
    similarity_score: float          # 0.0 - 1.0 (1.0 = identik)
    dyslexia_risk_score: float       # 0.0 - 100.0 (skor risiko klinis)
    error_types: list[str] = field(default_factory=list)
    error_details: list[ErrorDetail] = field(default_factory=list)
    error_summary: str = ""
    phonetic_units: list[str] = field(default_factory=list)


# ============================================================
# MESIN UTAMA
# ============================================================

class DyslexiaFuzzyMatcher:
    """
    Mesin pencocokan teks yang peka terhadap pola kesalahan disleksia
    dalam konteks Bahasa Indonesia.

    Alasan Desain:
      Kelas ini didesain stateless (tidak menyimpan state antar pemanggilan)
      sehingga thread-safe dan bisa dipakai oleh FastAPI async endpoints
      tanpa perlu lock atau mutex.
    """

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalisasi teks: lowercase, hapus karakter non-alfanumerik.
        Dipertahankan sebagai method terpisah untuk konsistensi normalisasi
        antara target dan hasil OCR.
        """
        return "".join(c for c in text.lower() if c.isalnum())

    @staticmethod
    def _tokenize_phonetically(word: str) -> list[str]:
        """
        Memecah kata menjadi unit fonetik Bahasa Indonesia.
        Digraf (NG, NY, KH, SY) diperlakukan sebagai SATU token.

        Alasan ('Why'):
          Jika 'NG' dihitung sebagai 2 karakter terpisah, maka kesalahan
          menulis 'BANGO' sebagai 'BANO' akan dihitung sebagai 1 penghapusan.
          Dengan fonetik, 'NG' adalah satu unit, jadi penghapusannya
          secara klinis berarti anak tidak menguasai digraf tersebut.
        """
        tokens = []
        i = 0
        word_lower = word.lower()
        while i < len(word_lower):
            found_digraph = False
            for digraph in INDONESIAN_DIGRAPHS:
                if word_lower[i:i + len(digraph)] == digraph:
                    tokens.append(digraph)
                    i += len(digraph)
                    found_digraph = True
                    break
            if not found_digraph:
                tokens.append(word_lower[i])
                i += 1
        return tokens

    @staticmethod
    def _detect_reversal_errors(
        target_clean: str,
        detected_clean: str
    ) -> list[ErrorDetail]:
        """
        Mendeteksi inversi/reversal huruf yang khas disleksia.

        Strategi: Bandingkan karakter per posisi pada string yang sama panjangnya.
        Jika berbeda dan pasangan (target_char, detected_char) ada di daftar
        DYSLEXIA_REVERSAL_PAIRS, catat sebagai reversal error.
        """
        errors = []
        min_len = min(len(target_clean), len(detected_clean))

        for i in range(min_len):
            t_char = target_clean[i]
            d_char = detected_clean[i]

            if t_char != d_char:
                pair_key = (t_char, d_char)
                if pair_key in DYSLEXIA_REVERSAL_PAIRS:
                    severity_weight = DYSLEXIA_REVERSAL_PAIRS[pair_key]
                    severity = "high" if severity_weight >= 1.5 else "medium"

                    errors.append(ErrorDetail(
                        error_type="reversal",
                        target_char=t_char,
                        detected_char=d_char,
                        position=i,
                        severity=severity,
                        description=(
                            f"Inversi huruf di posisi {i + 1}: "
                            f"'{t_char.upper()}' tertukar dengan '{d_char.upper()}'. "
                            f"{'Ini pola b/d khas disleksia.' if pair_key in [('b','d'),('d','b')] else 'Cek orientasi huruf.'}"
                        )
                    ))

        return errors

    @staticmethod
    def _detect_structural_errors(
        target_tokens: list[str],
        detected_tokens: list[str],
        target_clean: str,
        detected_clean: str
    ) -> list[ErrorDetail]:
        """
        Mendeteksi kesalahan struktural: omission, insertion, transposition.

        Alasan ('Why'):
          Membedakan omission (huruf hilang) dari insertion (huruf tambah)
          sangat penting secara klinis:
          - Omission >> Anak lupa/tidak melihat sebagian huruf (visual tracking issue).
          - Insertion >> Anak menambah huruf yang tidak ada (phonological confusion).
          - Transposition >> Anak menulis huruf dalam urutan salah (sequencing issue).
        """
        errors = []

        len_target = len(target_tokens)
        len_detected = len(detected_tokens)

        # Deteksi Omission (huruf hilang)
        if len_detected < len_target:
            missing_count = len_target - len_detected
            errors.append(ErrorDetail(
                error_type="omission",
                target_char="".join(target_tokens),
                detected_char="".join(detected_tokens),
                position=len_detected,
                severity="high" if missing_count > 1 else "medium",
                description=(
                    f"{missing_count} unit fonetik hilang. "
                    f"Target: '{target_clean.upper()}', Terbaca: '{detected_clean.upper() or '(kosong)'}'. "
                    "Anak kemungkinan melewati huruf saat menulis."
                )
            ))

        # Deteksi Insertion (huruf tambah)
        elif len_detected > len_target:
            extra_count = len_detected - len_target
            errors.append(ErrorDetail(
                error_type="insertion",
                target_char="".join(target_tokens),
                detected_char="".join(detected_tokens),
                position=len_target,
                severity="medium" if extra_count == 1 else "high",
                description=(
                    f"{extra_count} huruf tambahan terdeteksi. "
                    f"Target: '{target_clean.upper()}', Terbaca: '{detected_clean.upper()}'. "
                    "Anak kemungkinan menambah huruf karena kebingungan fonetik."
                )
            ))

        # Deteksi Transposition (urutan huruf terbalik — anagram)
        if (
            len_detected == len_target
            and sorted(target_clean) == sorted(detected_clean)
            and target_clean != detected_clean
        ):
            errors.append(ErrorDetail(
                error_type="transposition",
                target_char=target_clean,
                detected_char=detected_clean,
                position=0,
                severity="high",
                description=(
                    f"Urutan huruf terbalik (transposition): "
                    f"'{target_clean.upper()}' ditulis sebagai '{detected_clean.upper()}'. "
                    "Ini menunjukkan masalah pada pemrosesan urutan sekuensial."
                )
            ))

        return errors

    @staticmethod
    def _calculate_dyslexia_risk_score(
        similarity_ratio: float,
        error_details: list[ErrorDetail],
        target_clean: str,
        detected_clean: str
    ) -> float:
        """
        Menghitung skor risiko disleksia (0-100) yang lebih sensitif
        dibanding similarity ratio biasa.

        Alasan Formula:
          - Base score dari similarity ratio dibalik (100 - similarity*100)
            agar 0 = tidak berisiko, 100 = sangat berisiko.
          - Setiap reversal error menambahkan bonus penalti (severity-weighted)
            karena reversal adalah marker klinis disleksia yang lebih kuat
            dibanding typo biasa.
          - Kata yang SAMA SEKALI tidak terbaca mendapat skor maksimum (100).
        """
        if not detected_clean:
            return 100.0  # OCR tidak mendeteksi tulisan = risiko maksimum

        if target_clean == detected_clean:
            return 0.0  # Persis benar = tidak berisiko

        base_risk = (1.0 - similarity_ratio) * 100.0

        # Bobot penalti per tipe error
        severity_weight = {"low": 3.0, "medium": 7.0, "high": 12.0, "critical": 20.0}
        reversal_penalty = sum(
            severity_weight.get(e.severity, 5.0)
            for e in error_details
            if e.error_type == "reversal"
        )

        # Skor transposition lebih tinggi dari omission karena lebih khas disleksia
        structural_penalty = sum(
            severity_weight.get(e.severity, 5.0) * (1.5 if e.error_type == "transposition" else 1.0)
            for e in error_details
            if e.error_type in ("omission", "insertion", "transposition")
        )

        total_risk = base_risk + reversal_penalty + structural_penalty
        return min(100.0, round(total_risk, 1))

    def analyze(self, target_word: str, detected_word: str) -> MatchResult:
        """
        Entry point utama: Analisis satu pasang kata (target vs. hasil OCR).

        Args:
            target_word: Kata yang seharusnya ditulis anak (dari bank soal).
            detected_word: Teks yang terbaca oleh mesin OCR.

        Returns:
            MatchResult: Objek hasil analisis lengkap.
        """
        target_clean = self._normalize(target_word)
        detected_clean = self._normalize(detected_word)

        # Tokenisasi fonetik untuk analisis berbasis unit bahasa
        target_tokens = self._tokenize_phonetically(target_clean)
        detected_tokens = self._tokenize_phonetically(detected_clean)

        # Hitung similarity standar (Levenshtein-based)
        ratio = fuzz.ratio(target_clean, detected_clean) / 100.0

        # Kumpulkan semua error
        all_errors: list[ErrorDetail] = []
        all_errors.extend(self._detect_reversal_errors(target_clean, detected_clean))
        all_errors.extend(self._detect_structural_errors(
            target_tokens, detected_tokens, target_clean, detected_clean
        ))

        # Tentukan apakah jawaban dianggap benar
        # Kata pendek (<= 4 char): harus PERSIS benar (tidak ada toleransi reversal)
        # Kata panjang (> 4 char): boleh fuzzy >= 85%, KECUALI ada reversal error
        has_reversal = any(e.error_type == "reversal" for e in all_errors)
        if len(target_clean) <= 4:
            is_correct = (target_clean == detected_clean)
        else:
            is_correct = (ratio >= 0.85) and not has_reversal

        # Hitung risk score
        risk_score = self._calculate_dyslexia_risk_score(
            ratio, all_errors, target_clean, detected_clean
        )

        # Kumpulkan tipe error unik
        error_types = list({e.error_type for e in all_errors})

        # Buat ringkasan untuk guru
        error_summary = self._build_error_summary(
            is_correct, error_types, all_errors, target_word, detected_word
        )

        return MatchResult(
            target_word=target_word,
            detected_word=detected_word,
            is_correct=is_correct,
            similarity_score=round(ratio, 3),
            dyslexia_risk_score=risk_score,
            error_types=error_types,
            error_details=all_errors,
            error_summary=error_summary,
            phonetic_units=target_tokens,
        )

    def analyze_batch(
        self,
        word_pairs: list[tuple[str, str]]
    ) -> tuple[list[MatchResult], dict]:
        """
        Analisis batch untuk satu sesi screening (beberapa soal sekaligus).
        Mengembalikan daftar hasil per kata DAN ringkasan agregat sesi.

        Args:
            word_pairs: List tuple (target_word, detected_word).

        Returns:
            Tuple dari (list MatchResult, dict agregasi sesi).
        """
        results = [self.analyze(target, detected) for target, detected in word_pairs]

        if not results:
            return results, {}

        total = len(results)
        correct_count = sum(1 for r in results if r.is_correct)
        avg_risk = sum(r.dyslexia_risk_score for r in results) / total

        # Frekuensi tipe error di seluruh sesi
        error_frequency: dict[str, int] = {}
        for result in results:
            for error_type in result.error_types:
                error_frequency[error_type] = error_frequency.get(error_type, 0) + 1

        # Identifikasi error yang paling dominan
        dominant_error = max(error_frequency, key=error_frequency.get) if error_frequency else None

        # Klasifikasi level risiko sesi
        if avg_risk >= 70:
            session_risk_level = "Tinggi"
        elif avg_risk >= 40:
            session_risk_level = "Sedang"
        elif avg_risk >= 15:
            session_risk_level = "Rendah"
        else:
            session_risk_level = "Sangat Rendah"

        session_summary = {
            "total_words": total,
            "correct_count": correct_count,
            "accuracy_percent": round((correct_count / total) * 100, 1),
            "average_risk_score": round(avg_risk, 1),
            "session_risk_level": session_risk_level,
            "error_frequency": error_frequency,
            "dominant_error_type": dominant_error,
            "recommended_intervention": _get_intervention_recommendation(dominant_error, avg_risk),
        }

        return results, session_summary

    @staticmethod
    def _build_error_summary(
        is_correct: bool,
        error_types: list[str],
        error_details: list[ErrorDetail],
        target_word: str,
        detected_word: str
    ) -> str:
        """Membangun pesan ringkasan yang informatif untuk antarmuka guru."""
        if is_correct:
            return f"Tepat! Kata '{target_word.upper()}' ditulis dengan benar."

        if not error_types:
            return (
                f"Penulisan '{detected_word}' mendekati '{target_word.upper()}', "
                "namun ada ketidaksesuaian minor."
            )

        parts = []
        if "reversal" in error_types:
            reversals = [e for e in error_details if e.error_type == "reversal"]
            chars = ", ".join(
                f"'{e.target_char.upper()}' -> '{e.detected_char.upper()}'"
                for e in reversals
            )
            parts.append(f"Inversi huruf: {chars}")
        if "omission" in error_types:
            parts.append("Huruf hilang (omission)")
        if "insertion" in error_types:
            parts.append("Huruf tambahan (insertion)")
        if "transposition" in error_types:
            parts.append("Urutan huruf terbalik (transposition)")

        return f"Target '{target_word.upper()}': {' | '.join(parts)}."


# ============================================================
# HELPER: REKOMENDASI INTERVENSI
# ============================================================

def _get_intervention_recommendation(
    dominant_error: Optional[str],
    avg_risk: float
) -> str:
    """
    Menghasilkan rekomendasi intervensi berbasis metode Orton-Gillingham
    sesuai dengan pola kesalahan dominan yang terdeteksi dalam satu sesi.

    Alasan ('Why'):
      Rekomendasi yang tersedia di aplikasi tidak bisa hanya generik.
      Metode Orton-Gillingham (OG) adalah pendekatan berbasis bukti (evidence-based)
      untuk intervensi disleksia yang menggunakan kombinasi visual, auditori, dan
      kinestetik (VAK) — persis seperti yang diimplementasikan DyLeks.
    """
    recommendations = {
        "reversal": (
            "Latihan Taktil OG: Minta anak menelusuri huruf di bak pasir/tepung "
            "sambil menyebutkan namanya keras. Fokus pasang 'b' dan 'd' dengan "
            "mnemonik jari (telunjuk kiri=b, telunjuk kanan=d)."
        ),
        "omission": (
            "Latihan Segmentasi Fonem: Gunakan kotak Elkonin (kotak sekuensial) "
            "untuk memandu anak mengetuk setiap fonem. Latih tracking visual "
            "dari kiri ke kanan secara eksplisit."
        ),
        "insertion": (
            "Latihan Blending OG: Gunakan kartu fonem individual untuk membangun "
            "kata secara bertahap. Minta anak menyusun fisik, bukan hanya menulis, "
            "agar terbentuk representasi motor yang kuat."
        ),
        "transposition": (
            "Latihan Urutan Sekuensial: Gunakan penguatan warna pada suku kata "
            "(misal: merah=konsonan, biru=vokal). Latih pola CVC (Konsonan-Vokal-Konsonan) "
            "secara berulang dengan kartu kata bertingkat."
        ),
        "substitution": (
            "Latihan Fonetik Minimal Pairs: Bandingkan kata-kata yang hampir mirip "
            "bunyi (mis: 'buku' vs 'duku') secara auditori dan visual bersamaan "
            "untuk memperkuat pemetaan grafem-fonem."
        ),
    }

    if dominant_error and dominant_error in recommendations:
        return recommendations[dominant_error]

    if avg_risk < 20:
        return "Pertahankan latihan rutin! Lanjutkan ke level berikutnya."

    return (
        "Lakukan latihan multisensori umum: gabungkan visual (melihat huruf), "
        "auditori (mengeja keras), dan kinestetik (menulis di udara/pasir) "
        "secara bersamaan untuk memperkuat memori huruf."
    )


# ============================================================
# SINGLETON INSTANCE (Agar tidak re-inisialisasi setiap request)
# ============================================================
dyslexia_matcher = DyslexiaFuzzyMatcher()
