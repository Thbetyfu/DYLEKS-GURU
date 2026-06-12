"""
QR Connect Pydantic Schemas.
Kontrak data untuk endpoint generasi QR token dan penyambungan siswa.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QRTokenCreate(BaseModel):
    """Payload opsional saat membuat QR token (opsional mengaitkan child_id)."""
    child_id: Optional[str] = None

class QRTokenResponse(BaseModel):
    """Response detail QR token untuk guru."""
    token: str
    status: str
    expired_at: datetime

class StudentConnectRequest(BaseModel):
    """Payload saat HP siswa melakukan scan QR code."""
    token: str
    child_id: Optional[str] = None

class StudentConnectResponse(BaseModel):
    """Response sukses koneksi berisi token otorisasi luring."""
    status: str
    access_token: str
    child_name: str
