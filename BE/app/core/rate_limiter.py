"""
Memory-Based Local Rate Limiter Module.
Mengatur pembatasan laju (rate limiting) request API secara lokal
tanpa membutuhkan dependensi database Redis, cocok untuk daerah 3T.
"""

import time
from fastapi import Request, HTTPException, status
from typing import Dict, Tuple


class LocalRateLimiter:
    """
    Pembatas laju request sederhana berbasis algoritma Token Bucket per IP.
    """
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # Struktur: client_ip -> (jumlah_token_saat_ini, timestamp_terakhir_update)
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def _refill(self, ip: str) -> float:
        """Mengisi kembali token secara linier berdasarkan waktu elapsed."""
        now = time.time()
        if ip not in self.buckets:
            self.buckets[ip] = (float(self.requests_limit), now)
            return float(self.requests_limit)

        tokens, last_update = self.buckets[ip]
        elapsed = now - last_update
        
        # Laju pengisian token per detik
        refill_rate = self.requests_limit / self.window_seconds
        new_tokens = tokens + (elapsed * refill_rate)
        
        # Batasi token agar tidak melebihi kapasitas maksimum bucket
        if new_tokens > self.requests_limit:
            new_tokens = float(self.requests_limit)
            
        self.buckets[ip] = (new_tokens, now)
        return new_tokens

    def check_rate_limit(self, request: Request):
        """
        Pemeriksaan rate limit untuk request yang masuk.
        Melemparkan HTTPException 429 jika token tidak mencukupi.
        """
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # Proteksi kebocoran memori (memory leak) jika data klien terlalu banyak
        if len(self.buckets) > 1000:
            self.cleanup()

        tokens = self._refill(client_ip)
        
        if tokens < 0.999:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Terlalu banyak permintaan ke server. Silakan tunggu beberapa saat."
            )
            
        # Kurangi token setelah diizinkan lewat
        _, last_update = self.buckets[client_ip]
        self.buckets[client_ip] = (tokens - 1.0, last_update)

    def cleanup(self):
        """Membersihkan entri IP yang sudah lama tidak aktif."""
        now = time.time()
        expired_ips = [
            ip for ip, (_, last_update) in self.buckets.items()
            if now - last_update > self.window_seconds
        ]
        for ip in expired_ips:
            self.buckets.pop(ip, None)


# 1. Rate limiter khusus pengunggahan berkas gambar skrining (Sangat ketat)
# Maksimal 5 unggahan per 30 detik per IP client
upload_rate_limiter = LocalRateLimiter(requests_limit=5, window_seconds=30)

# 2. Rate limiter umum untuk rute API lainnya
# Maksimal 60 request per 60 detik per IP client
general_rate_limiter = LocalRateLimiter(requests_limit=60, window_seconds=60)
