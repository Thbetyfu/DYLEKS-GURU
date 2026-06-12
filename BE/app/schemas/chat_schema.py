"""
Chat Pydantic Schemas.
Mendefinisikan kontrak data untuk interaksi guru dengan AI Pedagogical Copilot.
"""

from pydantic import BaseModel
from typing import Optional

class ScreeningContext(BaseModel):
    """Konteks hasil skrining anak yang dikirim guru ke Copilot untuk rekomendasi spesifik."""
    child_name: Optional[str] = None    # Nama anak (opsional, untuk privasi)
    risk_level: Optional[str] = None    # "Rendah", "Sedang", "Tinggi"
    recommended_level: Optional[int] = None  # Level yang direkomendasikan (1-5)
    detected_errors: Optional[list[str]] = []  # Pola kesalahan yang terdeteksi

class ChatRequest(BaseModel):
    """Payload pesan guru ke AI Copilot, opsional dengan context skrining."""
    message: str
    child_id: Optional[str] = None
    context: Optional[ScreeningContext] = None  # Hasil skrining untuk rekomendasi spesifik

class ChatResponse(BaseModel):
    """Respon dari AI Pedagogical Copilot."""
    reply: str
    context_id: Optional[str] = None