"""
User (Guru) Model Definition.

Alasan ('Why'):
  Dalam sistem lokal kelas (Local Mesh Dashboard), setiap laptop guru
  bertindak sebagai server hub yang mengelola data PRIBADI anak-anak.
  Model User ini adalah 'penjaga pintu' (gatekeeper) utama:
  - Memastikan data siswa satu guru TIDAK bisa diakses oleh guru lain
    meskipun terhubung ke Wi-Fi lokal yang sama.
  - Menjadi akar relasi One-to-Many: 1 Guru -> Banyak ChildProfile.
  - Password di-hash dengan bcrypt agar aman disimpan di SQLite lokal.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """
    Entitas Guru/Admin yang mengoperasikan server DyLeks lokal.
    Satu instans User = Satu guru yang bertanggung jawab atas kelasnya.
    """
    __tablename__ = "users"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Identitas Guru
    full_name = Column(String(150), nullable=False)
    username = Column(String(80), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Metadata Profil
    school_name = Column(String(200), nullable=True)
    school_region = Column(String(200), nullable=True)  # Contoh: "Kab. Dayeuhkolot, Jawa Barat"

    # Kontrol Akses & Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    # Relasi: Satu Guru memiliki banyak profil siswa
    # cascade="all, delete-orphan" => Jika guru dihapus, data siswanya ikut terhapus
    children = relationship(
        "ChildProfile",
        backref="teacher",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
