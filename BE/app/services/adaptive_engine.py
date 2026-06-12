"""
Adaptive Learning Engine.
Menangani algoritma personalisasi pemilihan soal (Spaced Repetition) 
dan penilaian respons kognitif anak secara offline.
"""
import random
from sqlalchemy.orm import Session
from app.models.exercise import Exercise, LearningSession, ExerciseResponse
from typing import Optional

class AdaptiveEngine:
    """
    Mesin adaptif pengatur kurikulum multisensori Orton-Gillingham.
    """

    @staticmethod
    def get_next_exercises(db: Session, child_id: str, current_level: int, limit: int = 10) -> list[Exercise]:
        """
        Mengambil koleksi soal dengan rasio adaptif luring (80% level saat ini, 20% level pengulangan dasar).
        
        Alasan ('Why'):
          Anak disleksia memerlukan latihan berulang (spaced repetition) agar materi fonem
          dasar tidak terhapus dari memori jangka panjang saat mereka naik ke level yang lebih kompleks.
          Rasio 80/20 menjaga tantangan materi baru tetap tinggi sekaligus memperkuat fondasi lama.
        """
        if current_level <= 1:
            # Level 1 tidak memiliki level di bawahnya, ambil 100% dari Level 1
            return db.query(Exercise).filter(Exercise.level == 1).order_by(Exercise.id).limit(limit).all()

        # Tentukan target jumlah soal
        target_review = max(1, int(limit * 0.20))  # Minimal 1 soal pengulangan
        target_active = limit - target_review

        # Ambil soal dari level aktif secara acak
        active_pool = db.query(Exercise).filter(Exercise.level == current_level).all()
        active_sample = random.sample(active_pool, min(len(active_pool), target_active)) if active_pool else []

        # Ambil soal pengulangan dari level yang lebih rendah
        review_pool = db.query(Exercise).filter(Exercise.level < current_level).all()
        review_sample = random.sample(review_pool, min(len(review_pool), target_review)) if review_pool else []

        # Gabungkan dan acak urutannya agar anak tidak menyadari pola repetisi
        combined = active_sample + review_sample
        random.shuffle(combined)
        return combined

    @staticmethod
    def evaluate_answer(
        db: Session,
        exercise_id: str,
        user_answer: str,
        response_time_ms: int,
        grip_pressure: Optional[float] = None,
        grip_tremor: Optional[float] = None,
        grip_hesitation: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> dict:
        """
        Mengevaluasi jawaban siswa, menganalisis beban kognitif anak secara real-time via DDS,
        menyimpan respon ke database, dan mengembalikan feedback serta aksi adaptasi.
        """
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            return {"status": "error", "message": "Soal tidak ditemukan."}

        # Evaluasi case-insensitive
        is_correct = exercise.correct_answer.strip().lower() == user_answer.strip().lower()

        # Simpan respons ke database jika ada session_id
        if session_id:
            response_record = ExerciseResponse(
                session_id=session_id,
                exercise_id=exercise_id,
                user_answer=user_answer,
                is_correct=is_correct,
                response_time_ms=response_time_ms
            )
            db.add(response_record)
            db.commit()

        # 1. Metrik Keakuratan Historis (kesalahan beruntun)
        consecutive_errors = 0
        if session_id:
            recent_responses = (
                db.query(ExerciseResponse)
                .filter(ExerciseResponse.session_id == session_id)
                .order_by(ExerciseResponse.id.desc())
                .limit(2)
                .all()
            )
            for r in recent_responses:
                if not r.is_correct:
                    consecutive_errors += 1
                else:
                    break
        
        # Tambah respon saat ini jika salah
        if not is_correct:
            consecutive_errors += 1

        # 2. Metrik Deteksi Kelelahan / Kebingungan (DDS Logic)
        is_hesitant = response_time_ms > 7000 or (grip_hesitation is not None and grip_hesitation > 0.6)
        is_fatigued = (grip_tremor is not None and grip_tremor > 0.6) or \
                      (grip_pressure is not None and (grip_pressure < 0.2 or grip_pressure > 0.8))
        is_frustrated = consecutive_errors >= 2

        dds_active = False
        dds_action = None
        dds_message = None
        reduced_options = None

        if is_hesitant or is_fatigued or is_frustrated:
            dds_active = True
            if is_frustrated or is_hesitant:
                dds_action = "reduce_options"
                dds_message = "Jangan khawatir! Kakak bantu menyederhanakan pilihan ganda ya."
            else:
                dds_action = "play_audio_hint"
                dds_message = "Tanganmu lelah? Mari dengarkan suara petunjuk terlebih dahulu!"

            # Cari dan reduksi opsi jika terdapat opsi pilihan ganda
            if exercise.content and isinstance(exercise.content, dict) and "options" in exercise.content:
                options = exercise.content["options"]
                correct = exercise.correct_answer
                distractors = [opt for opt in options if opt.strip().lower() != correct.strip().lower()]
                if distractors:
                    import random
                    chosen_distractor = random.choice(distractors)
                    reduced_list = [correct, chosen_distractor]
                    random.shuffle(reduced_list)
                    reduced_options = reduced_list

        # Generate feedback
        if is_correct:
            feedback_msg = "Luar biasa! Jawabanmu sangat tepat."
        else:
            feedback_msg = f"Usahamu bagus! Jawaban yang benar adalah '{exercise.correct_answer}'."

        return {
            "status": "success",
            "is_correct": is_correct,
            "correct_answer": exercise.correct_answer,
            "feedback": feedback_msg,
            "dds_active": dds_active,
            "dds_action": dds_action,
            "dds_message": dds_message,
            "reduced_options": reduced_options,
            "consecutive_errors": consecutive_errors  # sync state DDS ke FE
        }


