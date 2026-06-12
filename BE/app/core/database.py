"""
Core Database Configuration Module.
Mengatur koneksi sesi SQLAlchemy ke PostgreSQL (Supabase/Local).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env
load_dotenv()

# URL koneksi database (ganti dengan URL Supabase kamu di .env nantinya)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../../shared_db/dyleks_shared.db")

# Inisialisasi engine SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # check_same_thread hanya diperlukan jika menggunakan fallback SQLite
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Mengonfigurasi SQLite database ke WAL mode agar konkurensi pembacaan
    dan penulisan berjalan tanpa hambatan locked database.
    """
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()


# Pembuatan pembuat sesi (SessionLocal) untuk setiap request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk pewarisan model-model ORM
Base = declarative_base()

def get_db():
    """
    Dependency generator untuk mendapatkan sesi database per request.
    Memastikan koneksi ditutup secara aman setelah operasi selesai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()