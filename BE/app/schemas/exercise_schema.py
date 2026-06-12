"""
Exercise & Learning Schemas.
Kontrak data untuk pengambilan soal dan pengiriman jawaban dari Next.js.
"""

from pydantic import BaseModel
from typing import List, Optional, Any

# ==========================================
# [CATATAN UNTUK FE]: DATA SOAL
# ==========================================
class ExerciseResponse(BaseModel):
    """Data soal yang dikirim ke FE."""
    id: str
    level: int
    type: str
    content: Any # Bisa berupa object berisi {text: "", audio_url: "", options: []}
    
    class Config:
        from_attributes = True

# ==========================================
# [CATATAN UNTUK FE]: KIRIM JAWABAN
# ==========================================
class SubmitAnswerRequest(BaseModel):
    """Payload saat anak menjawab soal dengan tambahan data sensor grip.
    
    Why session_id: DDS membutuhkan riwayat jawaban beruntun (consecutive errors)
    yang tersimpan per sesi di database agar deteksi frustrasi kognitif tidak
    hanya bergantung pada state frontend yang mudah hilang saat reload.
    """
    exercise_id: str
    answer: str
    response_time_ms: int
    session_id: Optional[str] = None
    grip_pressure: Optional[float] = None
    grip_tremor: Optional[float] = None
    grip_hesitation: Optional[float] = None

class SubmitAnswerResponse(BaseModel):
    """Respons hasil evaluasi jawaban dan rekomendasi DDS."""
    is_correct: bool
    correct_answer: Optional[str] = None
    feedback: str
    dds_active: bool
    dds_action: Optional[str] = None  # "reduce_options", "play_audio_hint", "show_visual_hint"
    dds_message: Optional[str] = None
    reduced_options: Optional[List[str]] = None
    consecutive_errors: int = 0  # Jumlah kesalahan beruntun untuk update state FE

class SessionResultResponse(BaseModel):
    """Hasil akhir setelah sesi latihan selesai."""
    session_id: str
    correct_count: int
    wrong_count: int
    accuracy: float