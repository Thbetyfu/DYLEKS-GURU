"""
Screening Session Model.
Mendefinisikan skema database SQLite untuk mencatat riwayat hasil skrining anak.
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from datetime import datetime, timezone
import uuid
from app.core.database import Base

class ScreeningSession(Base):
    """
    Sesi skrining tulis tangan anak.
    """
    __tablename__ = "screening_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id = Column(String(36), ForeignKey("child_profiles.id"), nullable=True)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20)) # "Rendah", "Sedang", "Tinggi"
    recommended_level = Column(Integer, default=1)
    feedback = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))