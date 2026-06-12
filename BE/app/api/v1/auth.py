"""
Auth & User Management API Router.

Alasan ('Why'):
  Router ini adalah gerbang pertama DyLeks. Ia mengelola:
  1. Registrasi Guru baru ke server lokal (POST /register).
  2. Login Guru dan penerbitan session token (POST /login).
  3. CRUD profil anak di bawah kepemilikan Guru yang sedang login.

  Desain 'teacher_id-centric': Setiap operasi CRUD pada ChildProfile
  diisolasi menggunakan teacher_id dari session token, bukan dari parameter URL.
  Ini mencegah guru A mengakses data siswa milik guru B secara tidak sengaja.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.child_profile import ChildProfile
from app.models.qr_token import QRConnectToken
from app.schemas.user_schema import (
    UserCreate, UserLogin, UserResponse,
    ChildProfileCreate, ChildProfileResponse
)
from app.schemas.qr_schema import (
    QRTokenCreate, QRTokenResponse,
    StudentConnectRequest, StudentConnectResponse
)
from app.services.auth_service import (
    hash_password, verify_password,
    create_session_token, decode_session_token
)
import secrets
from datetime import datetime, timezone, timedelta

router = APIRouter()


# ============================================================
# DEPENDENCY: Ekstrak user_id dari header Authorization
# ============================================================
def get_current_teacher(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency untuk melindungi endpoint yang butuh autentikasi.
    Membaca token dari header 'Authorization: Bearer <token>'.

    Alasan ('Why'):
      Menggunakan Header Authorization adalah standar REST API.
      Frontend cukup menyimpan token di localStorage dan menyertakannya
      di setiap request ke protected endpoint.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token autentikasi tidak ditemukan.")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_session_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kadaluarsa.")

    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Akun guru tidak ditemukan atau tidak aktif.")

    return user


# ============================================================
# AUTH ENDPOINTS
# ============================================================

@router.post("/register", response_model=UserResponse, status_code=201)
def register_teacher(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Mendaftarkan Guru baru ke server lokal DyLeks.
    Username harus unik dalam satu instans server.
    """
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Username '{payload.username}' sudah digunakan. Pilih username lain."
        )

    new_user = User(
        full_name=payload.full_name,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        school_name=payload.school_name,
        school_region=payload.school_region,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login_teacher(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Login Guru dan mengembalikan session token.
    Token disimpan di sisi FE dan digunakan untuk request berikutnya.
    """
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Username atau password salah.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun tidak aktif. Hubungi administrator.")

    # Update last_login timestamp
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_session_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "school_name": user.school_name,
        }
    }


# ============================================================
# CHILD PROFILE ENDPOINTS (Protected - Butuh Login Guru)
# ============================================================

@router.post("/children", response_model=ChildProfileResponse, status_code=201)
def create_child_profile(
    payload: ChildProfileCreate,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Menambahkan profil siswa baru di bawah kepemilikan Guru yang sedang login.
    teacher_id di-set otomatis dari session — Guru tidak perlu menginputnya.
    """
    child = ChildProfile(
        teacher_id=current_teacher.id,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        grade=payload.grade,
        teacher_notes=payload.teacher_notes,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


@router.get("/children", response_model=list[ChildProfileResponse])
def list_children(
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Mengambil daftar SEMUA siswa milik Guru yang sedang login.
    Tidak bisa mengakses siswa milik guru lain.
    """
    children = db.query(ChildProfile).filter(
        ChildProfile.teacher_id == current_teacher.id
    ).all()
    return children


@router.get("/children/{child_id}", response_model=ChildProfileResponse)
def get_child_profile(
    child_id: str,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Mengambil detail profil satu siswa — hanya jika siswa tersebut milik guru yang login.
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.teacher_id == current_teacher.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Profil siswa tidak ditemukan atau bukan milik Anda."
        )
    return child


@router.patch("/children/{child_id}", response_model=ChildProfileResponse)
def update_child_profile(
    child_id: str,
    payload: ChildProfileCreate,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Memperbarui data profil siswa (nama, usia, catatan guru, dll).
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.teacher_id == current_teacher.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Profil siswa tidak ditemukan.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(child, field, value)

    db.commit()
    db.refresh(child)
    return child


@router.delete("/children/{child_id}", status_code=204)
def delete_child_profile(
    child_id: str,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Menghapus profil siswa beserta seluruh riwayat sesinya (cascade delete).
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.teacher_id == current_teacher.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Profil siswa tidak ditemukan.")

    db.delete(child)
    db.commit()


@router.post("/children/{child_id}/recommend-og")
async def generate_og_recommendation(
    child_id: str,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Menghasilkan rekomendasi intervensi Orton-Gillingham (OG) otomatis berbasis AI
    berdasarkan profil risiko dan riwayat skrining anak.
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.teacher_id == current_teacher.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Profil siswa tidak ditemukan.")

    from app.models.screening_session import ScreeningSession
    latest_screening = db.query(ScreeningSession).filter(
        ScreeningSession.child_id == child_id
    ).order_by(ScreeningSession.created_at.desc()).first()

    detected_errors = []
    if latest_screening and latest_screening.feedback:
        detected_errors.append(latest_screening.feedback)

    # Buat context untuk copilot
    context = {
        "child_name": child.name,
        "risk_level": child.risk_level,
        "recommended_level": child.current_level,
        "detected_errors": detected_errors
    }

    # Buat pesan instruksi otomatis ke AI untuk menghasilkan intervensi terarah
    prompt_message = (
        f"Berikan draf rencana intervensi pengajaran Orton-Gillingham luring yang spesifik untuk siswa saya bernama {child.name}. "
        f"Siswa saat ini berusia {child.age or 'tidak diketahui'} tahun, duduk di {child.grade or 'SD'}, dengan status tingkat risiko disleksia '{child.risk_level}' "
        f"dan berada pada level pembelajaran kurikulum adaptif '{child.current_level}/5'. "
        f"Fokuslah pada aktivitas intervensi multisensori luring di kelas tanpa kuota internet."
    )

    from app.services.ollama_service import copilot_service
    ai_reply = await copilot_service.get_reply(
        message=prompt_message,
        context=context
    )

    return {"recommendation": ai_reply}


@router.get("/children/{child_id}/recommendations")
def get_psychologist_recommendations(
    child_id: str,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Mengambil semua rekomendasi klinis dari psikolog untuk siswa tertentu.
    Hanya bisa diakses oleh guru yang memiliki profil siswa tersebut.
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.teacher_id == current_teacher.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Profil siswa tidak ditemukan.")

    from app.models.psychologist import PsychologistRecommendation, Psychologist
    
    recs = db.query(PsychologistRecommendation).filter(
        PsychologistRecommendation.child_id == child_id
    ).order_by(PsychologistRecommendation.created_at.desc()).all()

    results = []
    for r in recs:
        psy = db.query(Psychologist).filter(Psychologist.id == r.psychologist_id).first()
        psy_name = psy.full_name if psy else "Psikolog"
        results.append({
            "id": r.id,
            "clinical_notes": r.clinical_notes,
            "medical_recommendations": r.medical_recommendations,
            "created_at": r.created_at.isoformat(),
            "psychologist_name": psy_name
        })

    return results


# ============================================================
# QR CODE CONNECTION ENDPOINTS (Laptop-to-Mobile Setup)
# ============================================================

@router.post("/qr/generate", response_model=QRTokenResponse)
def generate_qr_token(
    payload: QRTokenCreate,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Membuat token sekali pakai untuk penyambungan PWA siswa.
    Token ini valid selama 5 menit.
    """
    token_str = secrets.token_urlsafe(16)
    
    # Nonaktifkan token lama dari guru ini untuk merapikan database (clean-up)
    db.query(QRConnectToken).filter(
        QRConnectToken.teacher_id == current_teacher.id,
        QRConnectToken.status == "pending"
    ).update({"status": "expired"})
    
    new_qr = QRConnectToken(
        token=token_str,
        teacher_id=current_teacher.id,
        child_id=payload.child_id,
        status="pending",
        expired_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.add(new_qr)
    db.commit()
    db.refresh(new_qr)
    
    return {
        "token": new_qr.token,
        "status": new_qr.status,
        "expired_at": new_qr.expired_at
    }


@router.get("/qr/status/{token}")
def check_qr_token_status(
    token: str,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Mengecek status token (pending/used/expired).
    Dipanggil secara berkala (polling) oleh Dashboard Guru.
    """
    qr_record = db.query(QRConnectToken).filter(
        QRConnectToken.token == token,
        QRConnectToken.teacher_id == current_teacher.id
    ).first()
    
    if not qr_record:
        raise HTTPException(status_code=404, detail="Token tidak ditemukan.")
        
    # Cek expired secara pasif jika statusnya pending
    if qr_record.status == "pending" and datetime.utcnow() > qr_record.expired_at:
        qr_record.status = "expired"
        db.commit()
        db.refresh(qr_record)
        
    # Ambil info anak jika sudah diasosiasikan
    child_name = ""
    if qr_record.child_id:
        child = db.query(ChildProfile).filter(ChildProfile.id == qr_record.child_id).first()
        if child:
            child_name = child.name
            
    return {
        "status": qr_record.status,
        "child_id": qr_record.child_id,
        "child_name": child_name
    }


@router.post("/qr/connect", response_model=StudentConnectResponse)
def connect_student_device(payload: StudentConnectRequest, db: Session = Depends(get_db)):
    """
    Dipanggil oleh HP siswa (PWA) setelah memindai QR code.
    Menghubungkan perangkat siswa, mengembalikan JWT/session token akses.
    """
    qr_record = db.query(QRConnectToken).filter(
        QRConnectToken.token == payload.token
    ).first()
    
    if not qr_record:
        raise HTTPException(status_code=404, detail="Token QR tidak valid.")
        
    if qr_record.status != "pending" or datetime.utcnow() > qr_record.expired_at:
        if qr_record.status == "pending":
            qr_record.status = "expired"
            db.commit()
        raise HTTPException(status_code=400, detail="Token QR sudah kedaluwarsa atau telah digunakan.")
        
    # Tentukan child_id (bisa dikirim dari HP siswa atau dari default token)
    target_child_id = payload.child_id or qr_record.child_id
    if not target_child_id:
        raise HTTPException(status_code=400, detail="Profil siswa tidak teridentifikasi. Harap tentukan siswa.")
        
    child = db.query(ChildProfile).filter(
        ChildProfile.id == target_child_id,
        ChildProfile.teacher_id == qr_record.teacher_id
    ).first()
    
    if not child:
        raise HTTPException(status_code=404, detail="Profil siswa tidak ditemukan di bawah guru ini.")
        
    # Sukses: Tandai token sebagai used
    qr_record.status = "used"
    qr_record.child_id = target_child_id
    db.commit()
    
    # Terbitkan token otorisasi siswa menggunakan token guru sebagai basis delegasi
    student_access_token = create_session_token(qr_record.teacher_id)
    
    return {
        "status": "success",
        "access_token": student_access_token,
        "child_name": child.name
    }


@router.get("/qr/info/{token}")
def get_qr_token_info(token: str, db: Session = Depends(get_db)):
    """
    Public endpoint untuk dipanggil oleh HP siswa (PWA).
    Mengambil info token, status, profil anak yang dikaitkan,
    atau daftar profil anak milik guru yang membuat token jika belum dikaitkan.
    """
    qr_record = db.query(QRConnectToken).filter(
        QRConnectToken.token == token
    ).first()
    
    if not qr_record:
        raise HTTPException(status_code=404, detail="Token QR tidak ditemukan.")
        
    # Cek expired secara pasif
    if qr_record.status == "pending" and datetime.utcnow() > qr_record.expired_at:
        qr_record.status = "expired"
        db.commit()
        db.refresh(qr_record)
        
    child_name = ""
    children_list = []
    
    if qr_record.child_id:
        child = db.query(ChildProfile).filter(ChildProfile.id == qr_record.child_id).first()
        if child:
            child_name = child.name
    else:
        # Ambil daftar semua anak milik guru pembuat token agar anak bisa memilih namanya di HP
        children = db.query(ChildProfile).filter(
            ChildProfile.teacher_id == qr_record.teacher_id
        ).all()
        children_list = [{"id": c.id, "name": c.name} for c in children]
        
    # Cari nama guru/sekolah untuk konfirmasi visual di HP siswa
    teacher = db.query(User).filter(User.id == qr_record.teacher_id).first()
    school_name = teacher.school_name if teacher else "Sekolah Luring"
    teacher_name = teacher.full_name if teacher else "Guru"
    
    return {
        "status": qr_record.status,
        "child_id": qr_record.child_id,
        "child_name": child_name,
        "school_name": school_name,
        "teacher_name": teacher_name,
        "children": children_list,
        "is_expired": qr_record.status == "expired" or datetime.utcnow() > qr_record.expired_at
    }


class StudentSelfRegisterRequest(BaseModel):
    token: str
    name: str
    age: int
    gender: Optional[str] = None
    grade: Optional[str] = None


@router.post("/qr/register-student")
def register_student_via_qr(payload: StudentSelfRegisterRequest, db: Session = Depends(get_db)):
    """
    Registrasi mandiri siswa luring via QR Code kelas.
    Membuat profil siswa baru dan menerbitkan token otorisasi luring.
    """
    qr_record = db.query(QRConnectToken).filter(
        QRConnectToken.token == payload.token
    ).first()
    
    if not qr_record:
        raise HTTPException(status_code=404, detail="Token QR tidak valid.")
        
    if qr_record.status != "pending" or datetime.utcnow() > qr_record.expired_at:
        if qr_record.status == "pending":
            qr_record.status = "expired"
            db.commit()
        raise HTTPException(status_code=400, detail="Token QR sudah kedaluwarsa atau telah digunakan.")
        
    # Buat profil siswa baru
    new_child = ChildProfile(
        teacher_id=qr_record.teacher_id,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        grade=payload.grade,
        risk_score=0,
        risk_level="Belum Dianalisis",
        current_level=1
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)
    
    # Tandai QR token sebagai used
    qr_record.status = "used"
    qr_record.child_id = new_child.id
    db.commit()
    
    # Terbitkan token otorisasi siswa
    student_access_token = create_session_token(qr_record.teacher_id, role="student", exp_minutes=300)
    
    return {
        "status": "success",
        "access_token": student_access_token,
        "child_id": new_child.id,
        "child_name": new_child.name
    }


@router.get("/children/{child_id}/learning-sessions")
def get_child_learning_sessions(
    child_id: str,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Mengambil seluruh riwayat sesi latihan dan respons belajar luring siswa tertentu.
    
    Alasan ('Why'):
      Memungkinkan guru melihat grafik perkembangan belajar, tingkat akurasi rata-rata,
      dan melacak tipe kesalahan (inversi huruf/kata) secara personal per siswa dari Dashboard Guru.
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.teacher_id == current_teacher.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Profil siswa tidak ditemukan atau bukan di bawah wewenang Anda."
        )

    from app.models.exercise import LearningSession, ExerciseResponse, Exercise

    sessions = (
        db.query(LearningSession)
        .filter(LearningSession.child_id == child_id)
        .order_by(LearningSession.start_time.desc())
        .all()
    )

    results = []
    for s in sessions:
        responses_list = []
        for r in s.responses:
            ex_target = ""
            if r.exercise_id:
                ex = db.query(Exercise).filter(Exercise.id == r.exercise_id).first()
                if ex:
                    ex_target = ex.correct_answer

            responses_list.append({
                "id": r.id,
                "target": ex_target or r.user_answer,
                "attempt": r.user_answer,
                "is_correct": r.is_correct,
                "response_time_ms": r.response_time_ms
            })

        results.append({
            "id": s.id,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "total_score": s.total_score,
            "responses": responses_list
        })

    return results


