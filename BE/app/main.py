from fastapi import FastAPI, Depends, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api.v1 import auth, chat
from app.core.rate_limiter import general_rate_limiter
from contextlib import asynccontextmanager

# Load all models explicitly before creating tables
# URUTAN IMPORT PENTING: User harus di-load sebelum ChildProfile
# karena ChildProfile memiliki ForeignKey ke tabel users.
from app.models import user, child_profile, exercise, screening_session, qr_token, psychologist

# Inisialisasi Database: Membuat semua tabel yang belum ada
# (termasuk tabel 'users' yang baru ditambahkan)
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jalankan Hardware Diagnostic sebelum memuat OCR engine
    from app.services.hardware_diagnostic import run_diagnostic
    run_diagnostic()

    from app.services.trocr_service import get_trocr_engine
    print("[Startup] Menyiapkan Otak AI (TrOCR)...")
    get_trocr_engine()
    print("[Startup] Otak AI Siap!")
    yield

app = FastAPI(
    title="DyslexiAI Backend API",
    description=(
        "API untuk platform deteksi dini disleksia DyLeks. "
        "Berjalan 100% offline di jaringan Wi-Fi lokal kelas."
    ),
    version="1.2.0",
    lifespan=lifespan
)

# CORS: Membatasi akses origin hanya pada subnet IP privat lokal (RFC 1918)
# guna mencegah serangan CSRF/pembajakan API saat server terhubung ke internet.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"^https?://("
        r"localhost|127\.0\.0\.1|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"([a-zA-Z0-9-]+\.)?dyleks\.(id|local)"
        r")(:\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrasi Router dengan proteksi rate limiter lokal
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth & User Management"], dependencies=[Depends(general_rate_limiter.check_rate_limit)])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Tutor Chat"], dependencies=[Depends(general_rate_limiter.check_rate_limit)])

# Startup processes migrated to lifespan handler

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "version": "1.2.0",
        "message": "DyslexiAI API is running. Auth system aktif.",
    }

# =====================================================================
# CAPTIVE PORTAL & CONNECTIVITY CHECK MOCK ROUTING
# Membantu perangkat Android, iOS, dan Windows tetap terhubung ke
# jaringan Wi-Fi lokal kelas luring meskipun tidak ada akses internet.
# =====================================================================

@app.get("/generate_204", status_code=204)
@app.head("/generate_204", status_code=204)
def generate_204_endpoint():
    """Mock connectivity check untuk Android OS"""
    return Response(status_code=204)

@app.get("/gen_204", status_code=204)
@app.head("/gen_204", status_code=204)
def gen_204_endpoint():
    """Mock connectivity check alternatif untuk Android OS"""
    return Response(status_code=204)

@app.get("/hotspot-detect.html")
@app.get("/library/test/success.html")
def apple_captive_portal_endpoint():
    """Mock connectivity check untuk iOS / macOS (Apple Captive Portal)"""
    html_content = "<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>"
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/connecttest.txt")
def windows_ncsi_endpoint():
    """Mock connectivity check untuk Windows OS (NCSI)"""
    return PlainTextResponse(content="Microsoft Connect Test", status_code=200)

@app.get("/ncsi.txt")
def windows_ncsi_txt_endpoint():
    """Mock connectivity check alternatif untuk Windows OS (NCSI)"""
    return PlainTextResponse(content="Microsoft NCSI", status_code=200)

