import os
import sys
import pytest
from fastapi.testclient import TestClient
import base64

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/docs")
    assert response.status_code == 200


def test_hardware_diagnostic():
    # Test jalannya hardware diagnostic
    from app.services.hardware_diagnostic import run_diagnostic, get_total_ram_gb
    import os
    
    # Bersihkan env vars agar bersih sebelum test
    os.environ.pop("DISABLE_OLLAMA_VISION", None)
    os.environ.pop("OLLAMA_VISION_MODEL", None)
    
    run_diagnostic()
    
    ram = get_total_ram_gb()
    assert ram > 0
    
    disable_flag = os.getenv("DISABLE_OLLAMA_VISION")
    assert disable_flag in ("true", "false")
    
    vision_model = os.getenv("OLLAMA_VISION_MODEL")
    assert vision_model is not None

def test_sqlite_wal_mode():
    # Test bahwa mode WAL (Write-Ahead Logging) teraktifkan pada SQLite3
    from app.core.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
      bind_url = str(db.bind.url)
      if "sqlite" in bind_url:
        result = db.execute(text("PRAGMA journal_mode;")).scalar()
        assert result.lower() == "wal"
        
        sync_result = db.execute(text("PRAGMA synchronous;")).scalar()
        # PRAGMA synchronous=NORMAL mengembalikan nilai integer 1
        assert sync_result in (1, "NORMAL")
    finally:
      db.close()

def test_captive_portal_endpoints():
    # Test Android OS connectivity checks
    res_android = client.get("/generate_204")
    assert res_android.status_code == 204
    assert len(res_android.content) == 0

    res_android_alt = client.get("/gen_204")
    assert res_android_alt.status_code == 204

    # Test Apple iOS/macOS connectivity checks
    res_apple1 = client.get("/hotspot-detect.html")
    assert res_apple1.status_code == 200
    assert "text/html" in res_apple1.headers["content-type"]
    assert "Success" in res_apple1.text

    res_apple2 = client.get("/library/test/success.html")
    assert res_apple2.status_code == 200
    assert "Success" in res_apple2.text

    # Test Windows NCSI connectivity checks
    res_win = client.get("/connecttest.txt")
    assert res_win.status_code == 200
    assert "text/plain" in res_win.headers["content-type"]
    assert "Microsoft Connect Test" in res_win.text

    res_win_alt = client.get("/ncsi.txt")
    assert res_win_alt.status_code == 200
    assert "Microsoft NCSI" in res_win_alt.text




