"""
QR Connect Token Model.
Mengelola data token sekali pakai (One-Time Connection) 
untuk menghubungkan perangkat siswa secara luring ke server guru.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.core.database import Base

class QRConnectToken(Base):
    """
    Entitas penyimpan token autentikasi QR untuk siswa.
    Token bersifat sekali pakai (One-Time Token) dan berdurasi pendek.
    """
    __tablename__ = "qr_connect_tokens"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Token acak unik
    token = Column(String(100), unique=True, nullable=False, index=True)
    
    # Guru yang membuat token
    teacher_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Siswa yang dikaitkan (opsional di awal)
    child_id = Column(
        String(36),
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Status token: pending, used, expired
    status = Column(String(20), default="pending", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expired_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(minutes=5),
        nullable=False
    )
