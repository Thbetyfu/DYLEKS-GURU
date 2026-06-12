import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_header():
    """Fixture untuk mendaftarkan guru baru, login, dan mendapatkan header Authorization."""
    import secrets
    username = f"guru_{secrets.token_hex(4)}"
    
    # 1. Register
    reg_resp = client.post("/api/v1/auth/register", json={
        "full_name": "Guru Test QR",
        "username": username,
        "password": "securepassword123",
        "school_name": "SD Test QR",
        "school_region": "Wilayah Test QR"
    })
    assert reg_resp.status_code == 201
    
    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": "securepassword123"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def child_profile_id(auth_header):
    """Fixture untuk membuat satu profil siswa di bawah guru tes."""
    resp = client.post("/api/v1/auth/children", headers=auth_header, json={
        "name": "Siswa Test QR",
        "age": 8,
        "gender": "L",
        "grade": "Kelas 2 SD",
        "teacher_notes": "Catatan tes QR"
    })
    assert resp.status_code == 201
    return resp.json()["id"]

def test_qr_flow_complete(auth_header, child_profile_id):
    # 1. Generate Token QR
    gen_resp = client.post("/api/v1/auth/qr/generate", headers=auth_header, json={
        "child_id": child_profile_id
    })
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert "token" in data
    assert data["status"] == "pending"
    token = data["token"]
    
    # 2. Cek status token (harus pending)
    status_resp = client.get(f"/api/v1/auth/qr/status/{token}", headers=auth_header)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "pending"
    assert status_data["child_id"] == child_profile_id
    assert status_data["child_name"] == "Siswa Test QR"
    
    # 3. Hubungkan perangkat siswa (PWA client)
    conn_resp = client.post("/api/v1/auth/qr/connect", json={
        "token": token,
        "child_id": child_profile_id
    })
    assert conn_resp.status_code == 200
    conn_data = conn_resp.json()
    assert conn_data["status"] == "success"
    assert "access_token" in conn_data
    assert conn_data["child_name"] == "Siswa Test QR"
    
    # 4. Cek status token lagi (harus used sekarang)
    status_resp2 = client.get(f"/api/v1/auth/qr/status/{token}", headers=auth_header)
    assert status_resp2.json()["status"] == "used"
    
    # 5. Coba hubungkan ulang dengan token yang sama (harus gagal/One-Time token)
    conn_resp_retry = client.post("/api/v1/auth/qr/connect", json={
        "token": token,
        "child_id": child_profile_id
    })
    assert conn_resp_retry.status_code == 400
    assert "sudah kedaluwarsa atau telah digunakan" in conn_resp_retry.json()["detail"]


def test_qr_flow_generic(auth_header, child_profile_id):
    # 1. Generate Token QR Tanpa child_id (Generik)
    gen_resp = client.post("/api/v1/auth/qr/generate", headers=auth_header, json={})
    assert gen_resp.status_code == 200
    token = gen_resp.json()["token"]
    
    # 2. Siswa memanggil public endpoint info (tanpa auth header)
    info_resp = client.get(f"/api/v1/auth/qr/info/{token}")
    assert info_resp.status_code == 200
    info_data = info_resp.json()
    assert info_data["status"] == "pending"
    assert info_data["child_id"] is None
    assert len(info_data["children"]) >= 1
    assert any(c["id"] == child_profile_id for c in info_data["children"])
    assert info_data["school_name"] == "SD Test QR"
    assert info_data["teacher_name"] == "Guru Test QR"
    
    # 3. Siswa menghubungkan diri dengan memilih salah satu profil anak
    conn_resp = client.post("/api/v1/auth/qr/connect", json={
        "token": token,
        "child_id": child_profile_id
    })
    assert conn_resp.status_code == 200
    assert conn_resp.json()["status"] == "success"


def test_generate_og_recommendation(auth_header, child_profile_id):
    # Test endpoint rekomendasi intervensi Orton-Gillingham otomatis
    resp = client.post(f"/api/v1/auth/children/{child_profile_id}/recommend-og", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendation" in data
    assert isinstance(data["recommendation"], str)
    assert len(data["recommendation"]) > 0

