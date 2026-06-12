"""
Image Pre-Processor Service.
Membersihkan gambar dari noise sebelum dikirim ke AI Vision agar akurasi deteksi meningkat.
Teknik: Grayscale → OTSU Thresholding → Denoising.

Alasan ('Why'):
  Anak-anak memfoto dengan bayangan, latar meja kayu, dan kertas kusut.
  Jika gambar 'kotor' ini langsung dikirim ke AI, model akan terdistraksi
  oleh noise dan menghasilkan diagnosis yang salah.
  Dengan preprocessing ini, AI hanya akan 'melihat' tinta vs kertas putih,
  meningkatkan akurasi secara signifikan tanpa model baru.
"""

import cv2
import numpy as np


def preprocess_handwriting(image_bytes: bytes) -> bytes:
    """
    Menerima raw image bytes, mengembalikan bytes gambar yang sudah dibersihkan
    (Grayscale + OTSU Adaptive Threshold).
    
    Alur:
      1. Decode bytes → NumPy array (format BGR OpenCV)
      2. Convert ke Grayscale
      3. Gaussian Blur untuk menghilangkan noise halus
      4. OTSU Thresholding untuk memisahkan tinta dari kertas secara adaptif
      5. Encode kembali ke JPEG bytes
    """
    # Decode bytes ke gambar OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        # Jika gagal decode, kembalikan bahan mentah
        return image_bytes

    # Resize agar tidak terlalu besar (mempercepat inferensi AI)
    max_dim = 1024
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Gaussian blur untuk mengurangi noise tingkat piksel
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Gunakan Adaptive Thresholding Gaussian untuk menangani bayangan tidak merata pada kertas
    # blockSize=11 dan C=2 adalah nilai standar yang andal untuk tulisan tangan pensil di kertas putih
    thresh = cv2.adaptiveThreshold(
        blurred, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        11, 
        2
    )

    # Convert kembali ke 3-channel agar model vision bisa membaca sebagai gambar warna
    result_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    # Encode ke JPEG bytes
    _, encoded = cv2.imencode('.jpg', result_img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return encoded.tobytes()
