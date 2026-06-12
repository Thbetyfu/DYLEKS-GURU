"""
Learning & Exercise Models.
Mendefinisikan bank soal, sesi latihan, dan pencatatan respon anak.
"""

from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.core.database import Base

class Exercise(Base):
    """
    Bank soal yang dikelompokkan berdasarkan level (1-5).
    """
    __tablename__ = "exercises"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(Integer, index=True) # Level 1-5
    type = Column(String(50)) # 'visual', 'auditory', 'writing'
    content = Column(JSON) # Menyimpan teks soal, URL audio, atau pilihan jawaban
    correct_answer = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LearningSession(Base):
    """
    Mencatat satu sesi belajar anak (kumpulan beberapa soal).
    """
    __tablename__ = "learning_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id = Column(String(36), ForeignKey("child_profiles.id"), nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    total_score = Column(Float, default=0.0)
    
    responses = relationship("ExerciseResponse", back_populates="session")

class ExerciseResponse(Base):
    """
    Mencatat jawaban anak untuk setiap soal dalam satu sesi.
    """
    __tablename__ = "exercise_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("learning_sessions.id"))
    exercise_id = Column(String(36), ForeignKey("exercises.id"))
    user_answer = Column(String(255))
    is_correct = Column(Boolean) # <-- Diperbaiki di sini, tanpa db.
    response_time_ms = Column(Integer)

    session = relationship("LearningSession", back_populates="responses")