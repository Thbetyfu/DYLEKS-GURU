"""
Offline Sync Pydantic Schemas.
Mendefinisikan skema JSON untuk menerima antrean data skrining luring (batch) dari client PWA.
"""

from pydantic import BaseModel
from typing import Optional, List

class OfflineWordAttempt(BaseModel):
    """
    Satu percobaan kata saat luring (berisi gambar dan huruf target).
    """
    target_letter: str
    image_base64: str

class OfflineSessionPayload(BaseModel):
    """
    Payload satu sesi skrining yang diselesaikan saat luring.
    """
    id: str  # Client-side temporary UUID untuk pencocokan status di FE
    child_id: Optional[str] = None
    timestamp: str
    word_attempts: List[OfflineWordAttempt]

class SyncRequest(BaseModel):
    """
    Request batch sync yang menampung banyak sesi luring sekaligus.
    """
    sessions: List[OfflineSessionPayload]

class SyncedSessionDetail(BaseModel):
    """
    Detail sesi luring yang berhasil diproses dan disimpan di server lokal.
    """
    client_id: str
    db_id: str
    risk_score: float
    risk_level: str
    recommended_level: int
    feedback: str

class SyncResponse(BaseModel):
    """
    Response setelah batch sync selesai diproses.
    """
    status: str
    synced_count: int
    synced_sessions: List[SyncedSessionDetail]


class OfflineExerciseResponse(BaseModel):
    """
    Skema satu respons soal luring.
    """
    target: str
    attempt: str
    is_correct: bool
    response_time_ms: int


class OfflineLearningSessionPayload(BaseModel):
    """
    Payload satu sesi latihan luring.
    """
    id: str  # Client-side temporary UUID
    start_time: str
    end_time: Optional[str] = None
    total_score: float
    responses: List[OfflineExerciseResponse]


class LearningBatchSyncRequest(BaseModel):
    """
    Request batch sync untuk progres belajar latihan luring.
    """
    child_id: str
    sessions: List[OfflineLearningSessionPayload]
    current_level: int


class LearningSyncResponse(BaseModel):
    """
    Response setelah sinkronisasi latihan luring selesai.
    """
    status: str
    synced_count: int
