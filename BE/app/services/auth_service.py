"""
Auth Service: Password Hashing & Verification.

Alasan ('Why'):
  Di daerah 3T, laptop guru adalah server publik dalam jaringan Wi-Fi kelas.
  Siapapun yang terhubung ke Wi-Fi tersebut secara teknis bisa mencoba akses API.
  Bcrypt digunakan karena:
  1. Secara desain lambat (cost factor), sehingga resistant terhadap brute-force attack.
  2. Tidak membutuhkan library eksternal berat — cocok untuk low-spec server.
  3. Standar industri untuk menyimpan password di REST API.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Menghasilkan hash bcrypt dari password plaintext.
    Salt di-generate otomatis oleh bcrypt per hash (tidak perlu disimpan terpisah).
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)  # rounds=12 adalah sweet spot keamanan vs performa
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Memverifikasi apakah password plaintext cocok dengan hash yang tersimpan.
    Menggunakan perbandingan constant-time dari bcrypt untuk mencegah timing attack.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_session_token(user_id: str, role: str = "teacher", exp_minutes: int = 720) -> str:
    """
    Membuat token sesi sederhana berbasis user_id untuk komunikasi stateless.

    Alasan ('Why'):
      Kita sengaja TIDAK menggunakan JWT penuh (dengan RSA/ECDSA) karena:
      - Menambah overhead library (python-jose, cryptography) yang besar.
      - Di jaringan lokal offline, risiko token dicuri dari luar = nol.
      - Token ini hanya perlu valid selama satu sesi kelas berlangsung.
      Cukup gunakan HMAC-SHA256 dengan secret key lokal.
    """
    import hmac
    import hashlib
    import os
    import time

    secret = os.getenv("SESSION_SECRET", "dyleks-local-secret-2026")
    timestamp = str(int(time.time()))
    exp_timestamp = str(int(time.time()) + (exp_minutes * 60))
    payload = f"{user_id}:{role}:{timestamp}:{exp_timestamp}"
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{payload}:{signature}"


def decode_session_token(token: str) -> dict | None:
    """
    Mendekode dan memverifikasi token sesi.
    Mengembalikan dict berisi user_id, role, dan timestamp, atau None jika tidak valid atau kedaluwarsa.
    """
    import hmac
    import hashlib
    import os
    import time

    try:
        parts = token.split(":")
        if len(parts) != 5:
            return None

        user_id, role, timestamp, exp_timestamp, provided_sig = parts
        secret = os.getenv("SESSION_SECRET", "dyleks-local-secret-2026")
        payload = f"{user_id}:{role}:{timestamp}:{exp_timestamp}"
        expected_sig = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(provided_sig, expected_sig):
            return None
            
        if int(time.time()) > int(exp_timestamp):
            return None

        return {"user_id": user_id, "role": role, "timestamp": int(timestamp)}
    except Exception:
        return None

