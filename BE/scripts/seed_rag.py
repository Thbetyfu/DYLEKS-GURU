import os
import json
import httpx
from dotenv import load_dotenv

# Load env variables
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:1.5b")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PATH = os.path.join(BASE_DIR, "app", "data", "knowledge_base_source.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "app", "data", "knowledge_base.json")

def get_embedding(text: str) -> list:
    """Mengambil representasi vektor (embedding) dari Ollama secara lokal."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": text
    }
    try:
        response = httpx.post(f"{OLLAMA_URL}/api/embeddings", json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return data.get("embedding", [])
    except Exception as err:
        # Fallback jika model embedding khusus tidak terpasang, coba run dengan model generik
        print(f"[Embedding Error] Gagal memproses teks dengan model '{OLLAMA_MODEL}': {err}")
        raise err

def main():
    print(f"Memulai seeding RAG menggunakan Ollama Model: {OLLAMA_MODEL}...")
    
    if not os.path.exists(SOURCE_PATH):
        print(f"[Error] Berkas sumber tidak ditemukan di: {SOURCE_PATH}")
        return

    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    vector_db = []
    total = len(documents)
    
    # Buat direktori tujuan jika belum ada
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    for i, doc in enumerate(documents, 1):
        title = doc.get("title", "")
        content = doc.get("content", "")
        print(f"[{i}/{total}] Memproses: {title}")
        
        # Gabungkan judul dan konten untuk mendapatkan pencarian semantik yang lebih kaya
        combined_text = f"{title}. {content}"
        
        try:
            vector = get_embedding(combined_text)
            if not vector:
                print(f"Warning: Vector kosong dihasilkan untuk: {title}")
                continue
            
            enriched_doc = {
                "id": doc.get("id"),
                "category": doc.get("category"),
                "title": title,
                "content": content,
                "vector": vector
            }
            vector_db.append(enriched_doc)
        except Exception:
            print("[Error] Proses seeding dihentikan. Pastikan Ollama server aktif.")
            print("Silakan jalankan perintah berikut di terminal Anda:")
            print(f"  ollama run {OLLAMA_MODEL}")
            return

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(vector_db, f, indent=2, ensure_ascii=False)

    print(f"Sukses! Database vektor RAG disimpan di: {OUTPUT_PATH}")
    print(f"Total dokumen terindeks: {len(vector_db)} entri.")

if __name__ == "__main__":
    main()
