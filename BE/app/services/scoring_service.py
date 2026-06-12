"""
Scoring and Risk Assessment Service — Refactored.

Alasan ('Why'):
  Service ini sebelumnya mengimplementasikan logika fuzzy matching sendiri
  secara sederhana. Sekarang ia didelegasikan ke DyslexiaFuzzyMatcher
  yang jauh lebih akurat secara klinis. ScoringService menjadi
  'orchestrator' yang:
  1. Memanggil DyslexiaFuzzyMatcher untuk analisis per kata.
  2. Mengagreasi skor dari satu sesi (banyak kata) menjadi skor risiko tunggal.
  3. Menyimpan hasil ke database SQLite lokal.
"""
from app.services.fuzzy_matching import dyslexia_matcher, MatchResult


class ScoringService:
    """
    Layanan analisis pola kesalahan penulisan dan klasifikasi risiko disleksia.
    Mendelegasikan logika pencocokan ke DyslexiaFuzzyMatcher.
    """

    @staticmethod
    def calculate_risk(target_word: str, ocr_text: str) -> dict:
        """
        Analisis satu kata: bandingkan kata target dengan hasil OCR.
        Wrapper tipis di atas DyslexiaFuzzyMatcher.analyze() untuk
        kompatibilitas backward dengan kode pemanggil yang ada.

        Returns:
            dict dengan keys: score (float 0-100), errors (list[str]), is_match (bool)
        """
        result: MatchResult = dyslexia_matcher.analyze(target_word, ocr_text)

        # Ambil pesan deskriptif dari setiap error detail untuk ditampilkan di FE
        error_messages = [detail.description for detail in result.error_details]

        return {
            "score": result.dyslexia_risk_score,
            "errors": error_messages,
            "is_match": result.is_correct,
            # Data tambahan yang kini tersedia untuk Teacher's Copilot
            "similarity": result.similarity_score,
            "error_types": result.error_types,
            "error_summary": result.error_summary,
        }

    @staticmethod
    def calculate_session_risk(word_pairs: list[tuple[str, str]]) -> dict:
        """
        Analisis satu sesi screening (banyak kata).
        Mengembalikan ringkasan agregat termasuk rekomendasi intervensi OG.

        Args:
            word_pairs: List tuple (target_word, ocr_detected_word).

        Returns:
            dict ringkasan sesi lengkap dari DyslexiaFuzzyMatcher.analyze_batch().
        """
        _, session_summary = dyslexia_matcher.analyze_batch(word_pairs)
        return session_summary

    @staticmethod
    def classify_risk_level(risk_score: float) -> tuple[str, int]:
        """
        Memetakan skor risiko ke label bahasa (Rendah/Sedang/Tinggi)
        dan rekomendasi level kurikulum DyLeks (1-5).

        Returns:
            Tuple (risk_label: str, recommended_level: int)
        """
        if risk_score >= 75:
            return "Tinggi", 1
        elif risk_score >= 55:
            return "Sedang-Tinggi", 2
        elif risk_score >= 35:
            return "Sedang", 3
        elif risk_score >= 15:
            return "Rendah", 4
        else:
            return "Sangat Rendah", 5
