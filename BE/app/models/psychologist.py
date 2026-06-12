"""
Psychologist & PsychologistRecommendation Model Definition.

Alasan ('Why'):
  Peran Psikolog adalah peran klinis/medis profesional baru yang berfungsi untuk
  meninjau hasil analisis kesalahan motorik dan menuliskan rekomendasi medis/terapi.
  - Psychologist: Menyimpan akun kredensial psikolog beserta nomor lisensi/STR.
  - PsychologistRecommendation: Relasi One-to-Many dari ChildProfile untuk mencatat
    setiap rekomendasi medis/terapi yang diajukan oleh psikolog.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Psychologist(Base):
    """
    Entitas Psikolog Profesional yang mengkaji data klinis siswa.
    """
    __tablename__ = "psychologists"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Identitas Psikolog
    full_name = Column(String(150), nullable=False)
    username = Column(String(80), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Kredensial Medis
    license_number = Column(String(100), nullable=False)  # Nomor STR / Izin Praktik
    clinic_name = Column(String(200), nullable=True)     # Klinik / Lembaga Mitra

    # Kontrol Akses & Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relasi: Psikolog memberikan banyak rekomendasi
    recommendations = relationship(
        "PsychologistRecommendation",
        backref="psychologist",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class PsychologistRecommendation(Base):
    """
    Rekomendasi medis/klinis yang ditulis oleh Psikolog untuk anak tertentu.
    Satu Siswa (ChildProfile) -> Banyak Rekomendasi Medis (One-to-Many).
    """
    __tablename__ = "psychologist_recommendations"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Kepemilikan: Dikaitkan dengan profil siswa
    child_id = Column(
        String(36),
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Otoritas: Dikaitkan dengan psikolog yang memberi catatan
    psychologist_id = Column(
        String(36),
        ForeignKey("psychologists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Catatan Klinis & Rekomendasi Medis
    clinical_notes = Column(Text, nullable=False)            # Catatan gejala/observasi
    medical_recommendations = Column(Text, nullable=False)   # Rujukan medis/terapi latihan VAKT

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
