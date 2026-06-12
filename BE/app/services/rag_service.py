"""
RAG (Retrieval-Augmented Generation) Service.
Menangani pencarian kesamaan semantik secara luring tanpa dependensi biner.

Alasan ('Why'):
  Pustaka database vektor standar (Chroma/FAISS) memerlukan kompilasi biner C++
  yang sering kali gagal saat instalasi pip di laptop Windows guru tanpa Visual Studio.
  Dengan menggunakan pencarian kesamaan kosinus (Cosine Similarity) berbasis matematika murni
  di memori terhadap database JSON, kita menjamin portabilitas 100% luring dengan performa tinggi
  karena jumlah dokumen rujukan disleksia relatif kecil (< 100 entri).
"""

import os
import json
import math
import httpx
from typing import List, Dict, Optional

class RAGService:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2:1.5b")
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "data", "knowledge_base.json")
        self.documents: List[Dict] = []
        self.load_database()

    def load_database(self) -> None:
        """
        Memuat data dokumen bervektor dari file JSON ke memori.
        
        Mengapa ('Why'):
          Memuat seluruh data ke memori saat startup menjamin kecepatan pencarian yang instan
          tanpa I/O overhead yang lambat saat menangani request kueri interaktif dari guru.
        """
        if not os.path.exists(self.db_path):
            print(f"[RAG Service] Database vektor tidak ditemukan di: {self.db_path}. RAG dinonaktifkan sementara.")
            return
        
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            print(f"[RAG Service] Berhasil memuat {len(self.documents)} dokumen rujukan.")
        except Exception as err:
            print(f"[RAG Service] Gagal memuat database RAG: {err}")

    def _dot_product(self, v1: List[float], v2: List[float]) -> float:
        """Menghitung perkalian titik (dot product) antara dua vektor."""
        return sum(a * b for a, b in zip(v1, v2))

    def _magnitude(self, v: List[float]) -> float:
        """Menghitung nilai magnitudo (panjang) dari sebuah vektor."""
        return math.sqrt(sum(a * a for a in v))

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        Menghitung kesamaan arah (Cosine Similarity) antara dua vektor.
        Mengembalikan skor dalam rentang [-1.0, 1.0] di mana nilai yang mendekati 1.0
        menandakan kesamaan semantik yang kuat.
        """
        mag_1 = self._magnitude(v1)
        mag_2 = self._magnitude(v2)
        if not mag_1 or not mag_2:
            return 0.0
        return self._dot_product(v1, v2) / (mag_1 * mag_2)

    async def _get_query_embedding(self, query: str) -> List[float]:
        """Mengambil representasi vektor dari teks kueri menggunakan Ollama API."""
        payload = {
            "model": self.ollama_model,
            "prompt": query
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.ollama_url}/api/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [])
        except Exception as err:
            print(f"[RAG Service] Gagal mengambil embedding kueri: {err}")
            return []

    async def search(self, query: str, top_k: int = 2, min_score: float = 0.35) -> List[Dict]:
        """
        Melakukan pencarian dokumen rujukan yang paling relevan dengan kueri.
        
        Mengapa ('Why'):
          Membatasi jumlah dokumen yang disisipkan (top_k) dan menerapkan batas skor minimal (min_score)
          sangat penting untuk mencegah prompt melebih kapasitas memori konteks SLM (qwen2:1.5b)
          serta memastikan dokumen yang tidak relevan diabaikan.
        """
        if not self.documents:
            self.load_database()
            if not self.documents:
                return []

        query_vector = await self._get_query_embedding(query)
        if not query_vector:
            return []

        results = []
        for doc in self.documents:
            doc_vector = doc.get("vector")
            if not doc_vector:
                continue
            
            score = self._cosine_similarity(query_vector, doc_vector)
            if score >= min_score:
                results.append({
                    "score": score,
                    "title": doc.get("title"),
                    "content": doc.get("content"),
                    "category": doc.get("category")
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

rag_service = RAGService()
