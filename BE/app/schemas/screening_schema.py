"""
Screening Pydantic Schemas.
Mendefinisikan format JSON untuk input gambar tulisan tangan dan output hasil analisis.
"""

from pydantic import BaseModel
from typing import Optional

# ==========================================
# [CATATAN UNTUK FE]: FORMAT REQUEST (POST)
# ==========================================
class ScreeningRequest(BaseModel):
    """
    Payload yang harus dikirim FE saat anak selesai menulis.
    """
    child_id: Optional[str] = None  # Bisa None jika ini sesi coba-coba (belum login)
    image_base64: str               # String gambar dari canvas (contoh: "data:image/png;base64,iVBORw0KG...")
    target_letter: str = "A"        # Target huruf (contoh: "A", "I", "U", "E", "O")

# ==========================================
# [CATATAN UNTUK FE]: FORMAT RESPONSE
# ==========================================
class ScreeningResponse(BaseModel):
    """
    Hasil balasan dari BE setelah gambar dianalisis oleh AI.
    """
    status: str
    risk_score: float        # Skor 0 - 100
    risk_level: str          # "Rendah", "Sedang", atau "Tinggi"
    recommended_level: int   # Rekomendasi level belajar (1-5)
    feedback: str            # Pesan ramah/saran untuk orang tua
    detected_errors: list[str] = [] # Daftar pola kesalahan visual yang ditemukan

class ScreeningSessionSubmit(BaseModel):
    """
    Payload submit hasil sesi skrining agregat dari online flow.
    """
    child_id: Optional[str] = None
    risk_score: float
    risk_level: str
    recommended_level: int
    feedback: str

class ScreeningSessionResponse(BaseModel):
    """
    Hasil analisis sesi skrining agregat yang disimpan ke database.
    """
    status: str
    session_id: str
    risk_score: float
    risk_level: str
    recommended_level: int
    feedback: str