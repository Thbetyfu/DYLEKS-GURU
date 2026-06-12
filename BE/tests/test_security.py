import os
import sys
import pytest
import sqlite3
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import SessionLocal, SQLALCHEMY_DATABASE_URL
from app.models.child_profile import ChildProfile

client = TestClient(app)


def test_cors_private_subnets():
    """Memverifikasi bahwa CORS membolehkan origin lokal privat dan menolak domain publik."""
    # 1. Valid local IP origins
    valid_origins = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://192.168.1.100:3001",
        "http://10.0.0.5:3001",
        "http://dyleks.local:3001",
        "http://dyleks.id"
    ]
    for origin in valid_origins:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin

    # 2. Invalid origins (e.g. internet malicious website)
    invalid_origins = [
        "http://evil-attacker.com",
        "https://google.com",
        "http://192.169.1.1:3001", # Di luar range privat
    ]
    for origin in invalid_origins:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        # CORSMiddleware tidak akan menyertakan header CORS pada origin tidak terdaftar
        assert "access-control-allow-origin" not in response.headers


def test_rate_limiting_trigger():
    """Memverifikasi rate limiter lokal menolak request berlebih dengan status 429."""
    from app.core.rate_limiter import general_rate_limiter
    
    original_limit = general_rate_limiter.requests_limit
    original_window = general_rate_limiter.window_seconds
    
    try:
        general_rate_limiter.requests_limit = 5
        general_rate_limiter.window_seconds = 30
        general_rate_limiter.buckets.clear()

        # Lakukan request login kosong berulang kali
        for i in range(5):
            response = client.post("/api/v1/auth/login", json={})
            assert response.status_code == 422

        # Request ke-6 harus memicu Rate Limiter 429 Too Many Requests
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 429
        assert "Terlalu banyak permintaan" in response.json()["detail"]
    finally:
        general_rate_limiter.requests_limit = original_limit
        general_rate_limiter.window_seconds = original_window


def test_database_transparent_encryption():
    """
    Memverifikasi enkripsi transparan di SQLite:
    - Data terbaca jelas lewat SQLAlchemy session (dekripsi transparan).
    - Data berupa cipher text tidak terbaca ketika diakses via raw sqlite3 (mentah).
    """
    db = SessionLocal()
    try:
        # 1. Masukkan profil baru lewat SQLAlchemy
        test_child = ChildProfile(
            name="Daniel Pratama",
            age=9,
            gender="L",
            grade="Kelas 3 SD",
            teacher_notes="Kesulitan menulis huruf b dan d."
        )
        db.add(test_child)
        db.commit()
        db.refresh(test_child)

        child_id = test_child.id

        # 2. Baca kembali lewat SQLAlchemy (harus terdekripsi transparan)
        retrieved_child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
        assert retrieved_child is not None
        assert retrieved_child.name == "Daniel Pratama"
        assert retrieved_child.teacher_notes == "Kesulitan menulis huruf b dan d."

        # 3. Kueri berkas SQLite secara mentah (raw connection)
        # Menghubungkan langsung ke file database SQLite luring menggunakan driver sqlite3
        db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, teacher_notes FROM child_profiles WHERE id = ?", (child_id,))
        raw_row = cursor.fetchone()
        conn.close()

        assert raw_row is not None
        raw_name, raw_notes = raw_row

        # Memastikan data yang tersimpan di disk terenkripsi (tidak sama dengan plain text)
        assert raw_name != "Daniel Pratama"
        assert raw_notes != "Kesulitan menulis huruf b dan d."
        # Memastikan format data terenkripsi dimulai dengan header cipher/Fernet (misal gAAAA...)
        assert raw_name.startswith("gAAAA")
        assert raw_notes.startswith("gAAAA")

        # Hapus data testing agar bersih
        db.delete(retrieved_child)
        db.commit()
    finally:
        db.close()
