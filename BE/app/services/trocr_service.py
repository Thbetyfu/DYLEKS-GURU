import os
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel, logging
from PIL import Image, ImageOps
from rapidfuzz import fuzz
import io
import traceback
import numpy as np
import cv2
from dotenv import load_dotenv

# Muat variabel dari .env
load_dotenv()
hf_token = os.getenv("HF_TOKEN")

# Matikan log peringatan yang tidak kritis
logging.set_verbosity_error()

# Singleton pattern untuk pemuatan model agar hemat memori (RAM)
_trocr_processor = None
_trocr_model = None

def get_trocr_engine():
    global _trocr_processor, _trocr_model
    if _trocr_model is None:
        print("[TrOCR] Inisialisasi Engine Transformers...")
        
        # Gunakan 'token' sebagai pengganti 'use_auth_token' (standar terbaru)
        # Hanya kirim jika token tersedia
        auth_kwargs = {"token": hf_token} if hf_token else {}

        _trocr_processor = TrOCRProcessor.from_pretrained(
            "microsoft/trocr-base-handwritten", 
            **auth_kwargs
        )
        _trocr_model = VisionEncoderDecoderModel.from_pretrained(
            "microsoft/trocr-base-handwritten",
            **auth_kwargs
        )
        
        # Pindahkan ke GPU jika ada untuk kecepatan maksimal (deteksi otomatis)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _trocr_model.to(device)
        print(f"[TrOCR] Model berhasil dimuat di: {device.upper()}")
        
    return _trocr_processor, _trocr_model

def improve_image_contrast(image: Image.Image) -> Image.Image:
    """
    Optimasi gambar sebelum inferensi: Normalkan kontras agar 
    tinta lebih menonjol dibanding bayangan kertas.
    """
    # Convert ke grayscale jika belum
    gray = ImageOps.grayscale(image)
    # Autocontrast untuk mempertegas tinta
    autocontrasted = ImageOps.autocontrast(gray, cutoff=2)
    return autocontrasted.convert("RGB")

async def analyze_with_trocr(image_bytes: bytes, target_word: str) -> dict:
    """
    State-of-the-Art Handwriting Recognition dengan optimasi Fuzzy Logic.
    """
    try:
        processor, model = get_trocr_engine()
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # 1. Konversi bytes ke PIL Image & Sharpening
        raw_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = improve_image_contrast(raw_image)

        # 2. Preprocessing & Prediction (Optimized)
        pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
        
        # Gunakan Beam Search (num_beams=5) untuk mencari kemungkinan teks terbaik
        # early_stopping=True mempercepat jika probabilitas sudah tinggi
        generated_ids = model.generate(
            pixel_values, 
            max_new_tokens=64,
            num_beams=5,
            early_stopping=True
        )
        
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # 3. Validasi & Fuzzy Matching (Akurasi Tinggi)
        # Menghapus spasi dan tanda baca pengganggu (mis: 'a b.' -> 'ab')
        output_clean = "".join(filter(str.isalnum, generated_text.lower()))
        target_clean = "".join(filter(str.isalnum, target_word.lower()))

        # Rasio kemiripan menggunakan Levenshtein Distance (0-100)
        similarity_ratio = fuzz.ratio(target_clean, output_clean)
        partial_ratio = fuzz.partial_ratio(target_clean, output_clean)
        
        # Syarat Lolos (Match): Kenalan langsung ATAU kemiripan sangat tinggi (>80%)
        # Hal ini menangani kasus 'ba' terdeteksi 'a b.'
        from app.services.scoring_service import ScoringService
        analysis = ScoringService.calculate_risk(target_word, generated_text)

        return {
            "score": analysis["score"],
            "errors": analysis["errors"],
            "engine": "trocr-transformer",
            "debug": {
                "all_text": generated_text,
                "similarity": round(similarity_ratio, 2)
            }
        }

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"[TrOCR Service Error]\n{error_msg}")
        return {
            "score": 50.0,
            "errors": [f"Kesalahan internal mesin TrOCR: {str(e)}"],
            "engine": "trocr-error"
        }

