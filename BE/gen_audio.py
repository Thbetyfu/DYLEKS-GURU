import os
from gtts import gTTS

# Direktori audio frontend: gunakan variabel lingkungan `FRONTEND_ASSETS_DIR`
# atau default ke folder `../FE/public/assets/audio` relatif terhadap folder `BE/`.
default_assets = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'FE', 'public', 'assets', 'audio'))
output_dir = os.environ.get('FRONTEND_ASSETS_DIR', default_assets)
os.makedirs(output_dir, exist_ok=True)

# List 5 target audio
kata_target = ['A', 'BA', 'BAN', 'NYALA', 'MENEMANI']

print("--- Memulai Generasi Audio Screening ---")

for kata in kata_target:
    # Suara murni target kata agar anak fokus pada bunyinya
    text = f"{kata}"
    tts = gTTS(text=text, lang='id', slow=False)
    
    file_name = f"instruksi_{kata.lower()}.mp3"
    file_path = os.path.join(output_dir, file_name)
    
    tts.save(file_path)
    print(f"✅ Berhasil: {file_name}")

print("\n--- Audio Sinkronisasi Selesai ---")
