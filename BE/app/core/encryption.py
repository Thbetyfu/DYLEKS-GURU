"""
Hardware-Bound Data Encryption Module.
Mengatur enkripsi AES-256 (Fernet) transparan untuk data sensitif di database
yang terikat pada Hardware ID (HWID) laptop Windows guru.
"""

import os
import sys
import hashlib
import base64
from cryptography.fernet import Fernet

try:
    import winreg
except ImportError:
    winreg = None


def get_machine_guid() -> str:
    """
    Mengambil UUID unik mesin Windows (MachineGuid) dari Windows Registry.
    Bila dijalankan di luar Windows, mengembalikan nilai fallback yang aman.
    """
    if winreg is not None:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                return guid.strip()
        except Exception:
            pass
    return "fallback_default_machine_guid_for_dyleks"


def get_encryption_key() -> bytes:
    """
    Menurunkan kunci enkripsi 32-byte URL-safe base64 dari gabungan
    MachineGuid (HWID) laptop dan variabel rahasia DB_ENCRYPTION_KEY di .env.
    """
    hwid = get_machine_guid()
    master_key = os.getenv("DB_ENCRYPTION_KEY", "default_secret_master_key_for_dyleks")
    
    # Gabungkan HWID dan master key untuk hashing SHA-256
    key_material = f"{hwid}:{master_key}".encode("utf-8")
    hashed = hashlib.sha256(key_material).digest()
    
    return base64.urlsafe_b64encode(hashed)


_fernet_instance = None


def _get_fernet() -> Fernet:
    """Mengembalikan atau membuat instansi Fernet secara singleton."""
    global _fernet_instance
    if _fernet_instance is None:
        key = get_encryption_key()
        _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_data(plain_text: str) -> str:
    """
    Mengenkripsi string teks biasa menjadi berkas cipher aman.
    """
    if not plain_text:
        return plain_text
    try:
        f = _get_fernet()
        return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        print(f"[Encryption Error] Gagal mengenkripsi data: {e}")
        return plain_text


def decrypt_data(cipher_text: str) -> str:
    """
    Mendekripsi berkas cipher aman kembali ke teks biasa.
    Jika bukan cipher text valid, mengembalikan teks asli.
    """
    if not cipher_text:
        return cipher_text
    try:
        f = _get_fernet()
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        # Jika gagal mendekripsi (karena datanya bukan ciphertext),
        # kembalikan teks asli (untuk kompatibilitas data lama).
        return cipher_text
