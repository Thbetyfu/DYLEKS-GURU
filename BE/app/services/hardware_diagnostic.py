"""
Hardware Diagnostic Service.
Mendeteksi spesifikasi fisik laptop server guru luring (RAM, CPU, GPU) saat startup
untuk menentukan pilihan model AI vision secara dinamis demi menjaga performa luring.
"""

import os
import ctypes
import sys
import multiprocessing

# Deklarasi struktur memori Windows untuk pembacaan RAM fisik
try:
    from ctypes import wintypes
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_uint64),
            ("ullAvailPhys", ctypes.c_uint64),
            ("ullTotalPageFile", ctypes.c_uint64),
            ("ullAvailPageFile", ctypes.c_uint64),
            ("ullTotalVirtual", ctypes.c_uint64),
            ("ullAvailVirtual", ctypes.c_uint64),
            ("ullAvailExtendedVirtual", ctypes.c_uint64),
        ]
except ImportError:
    MEMORYSTATUSEX = None

def get_total_ram_gb() -> float:
    """
    Mengambil total RAM fisik komputer dalam satuan GigaByte (GB).
    """
    if sys.platform == "win32" and MEMORYSTATUSEX is not None:
        try:
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return round(stat.ullTotalPhys / (1024 ** 3), 2)
        except Exception as e:
            print(f"[Diagnostic Debug] Gagal membaca win32 GlobalMemoryStatusEx: {e}")
            pass
            
    # Fallback 1: Jika library psutil tersedia
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except ImportError:
        pass

    # Fallback 2: Default netral (asumsi RAM mencukupi)
    return 8.0

def run_diagnostic():
    """
    Melakukan diagnosa hardware (RAM, CPU, GPU) pada laptop server guru luring,
    dan mengatur konfigurasi AI engine secara dinamis melalui environment variables.
    """
    print("=" * 60)
    print("[Hardware Diagnostic] Memulai pemindaian spesifikasi hardware server...")
    
    # 1. Deteksi Core CPU
    cpu_cores = multiprocessing.cpu_count()
    print(f"[Hardware Diagnostic] Jumlah CPU Cores: {cpu_cores}")
    
    # 2. Deteksi Kapasitas RAM Fisik
    ram_gb = get_total_ram_gb()
    print(f"[Hardware Diagnostic] Total RAM Fisik: {ram_gb} GB")
    
    # 3. Deteksi Ketersediaan GPU CUDA
    has_cuda = False
    try:
        import torch
        has_cuda = torch.cuda.is_available()
    except ImportError:
        pass
    print(f"[Hardware Diagnostic] GPU CUDA Terdeteksi: {has_cuda}")
    
    # 4. Pengambilan Keputusan Model Vision AI (Adaptive Fallback)
    # Kondisi RAM rendah (< 7.5 GB): Bypass Ollama Vision sepenuhnya, gunakan TrOCR
    if ram_gb < 7.5:
        print("[Hardware Diagnostic] KEPUTUSAN: RAM rendah (< 8GB).")
        print("[Hardware Diagnostic] Tindakan: Menonaktifkan Ollama Vision secara otomatis (bypassed).")
        os.environ["DISABLE_OLLAMA_VISION"] = "true"
        os.environ["OLLAMA_VISION_MODEL"] = "none"
    # RAM cukup dengan dukungan GPU CUDA: Gunakan model Vision utama LLaVA
    elif has_cuda:
        print("[Hardware Diagnostic] KEPUTUSAN: RAM mencukupi dan GPU CUDA aktif.")
        print("[Hardware Diagnostic] Tindakan: Mengaktifkan model vision utama (llava).")
        os.environ["DISABLE_OLLAMA_VISION"] = "false"
        os.environ["OLLAMA_VISION_MODEL"] = "llava"
    # RAM cukup tanpa GPU (CPU-only): Gunakan moondream yang super ringan (~1.7GB)
    else:
        print("[Hardware Diagnostic] KEPUTUSAN: RAM mencukupi namun berjalan dalam mode CPU-only.")
        print("[Hardware Diagnostic] Tindakan: Mengaktifkan model vision ringan (moondream).")
        os.environ["DISABLE_OLLAMA_VISION"] = "false"
        os.environ["OLLAMA_VISION_MODEL"] = "moondream"
    
    print("=" * 60)
