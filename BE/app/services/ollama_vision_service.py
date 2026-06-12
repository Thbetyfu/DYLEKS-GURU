"""
Ollama Vision Service — Pengganti Gemini (100% Offline, Zero API Key).
Menganalisis gambar tulisan tangan anak menggunakan model vision lokal via Ollama.

Model yang didukung (direkomendasikan diinstal salah satu):
  - moondream    (~1.7GB) : Paling ringan, cocok laptop 4-8GB RAM
  - llava-phi3   (~3.8GB) : Lebih akurat, cocok laptop 8GB+ RAM
  - llava:7b     (~4.5GB) : Paling akurat, butuh RAM 8GB+

Cara install: ollama pull moondream
"""

import httpx
import base64
import os
import json
import re

# Model vision yang digunakan (bisa di-override via .env)
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "moondream")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

ANALYSIS_PROMPT = """Kamu adalah sistem AI untuk mendeteksi pola tulisan tangan anak yang mengindikasikan disleksia.

Anak diminta menulis: "{target_letter}"

Analisis gambar tulisan tangan ini dan jawab HANYA dengan JSON berikut (tanpa markdown, tanpa teks lain):
{{
  "risk_score": <angka 0-100, dimana 0=sangat baik, 100=risiko disleksia sangat tinggi>,
  "detected_errors": [<daftar string pola kesalahan yang terdeteksi, kosong jika tidak ada>]
}}

Panduan penilaian:
- 0-20 : Tulisan sangat jelas dan tepat, tidak ada indikasi disleksia
- 21-40: Ada sedikit ketidakrapian, namun masih dalam batas normal
- 41-60: Terdeteksi inkonsistensi: huruf kurang proporsional, garis ragu-ragu
- 61-80: Ada pola disleksia: huruf terbalik, urutan salah, atau cerminan
- 81-100: Indikasi kuat disleksia: huruf tidak dapat dikenali atau sangat terdistorsi

Contoh detected_errors: ["Huruf b tertulis terbalik seperti d", "Garis vertikal tidak stabil", "Spasi antar huruf tidak konsisten"]

Jika gambar bukan tulisan tangan (foto benda, wajah, dll): set risk_score=100 dan detected_errors=["Gambar tidak relevan. Foto ulang tulisan di kertas putih."]"""


async def analyze_dyslexia_image(image_bytes: bytes, target_letter: str = "A") -> dict:
    """
    Analisis gambar tulisan tangan menggunakan Ollama Vision Model (offline).

    Alasan ('Why'):
      Menggantikan Gemini API dengan model vision lokal agar DyLeks benar-benar
      bebas dari ketergantungan internet dan API key berbayar — sesuai kebutuhan
      sekolah di daerah 3T yang tidak memiliki akses internet stabil.
    """
    # Encode image ke base64 string (format yang diterima Ollama)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = ANALYSIS_PROMPT.format(target_letter=target_letter)

    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [b64_image],
        "stream": False,
        "options": {
            "temperature": 0.1,  # Rendah agar output konsisten dan tidak halusinasi
            "num_predict": 256,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            raw_text = data.get("response", "").strip()

        # Ekstrak JSON dari response (model kadang menambahkan teks sebelum/sesudah JSON)
        json_match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
        if not json_match:
            raise ValueError(f"Model tidak mengembalikan JSON valid. Response: {raw_text[:200]}")

        result = json.loads(json_match.group())

        return {
            "score": float(result.get("risk_score", 50.0)),
            "errors": result.get("detected_errors", []),
            "engine": f"ollama-vision/{VISION_MODEL}"
        }

    except httpx.ConnectError:
        # Ollama tidak berjalan — fallback ke TrOCR ditangani di screening.py
        raise RuntimeError(
            f"Ollama tidak dapat dijangkau di {OLLAMA_BASE_URL}. "
            "Pastikan Ollama sudah berjalan dan model vision sudah diinstal."
        )
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Parsing JSON dari model vision gagal: {e}")
