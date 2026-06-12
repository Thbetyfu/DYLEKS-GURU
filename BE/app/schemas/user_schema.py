"""
Pydantic Schemas untuk User (Guru) API.

Alasan ('Why'):
  Schemas memisahkan 'data yang dikirim lewat jaringan' dari 'data yang disimpan
  di database'. Ini mencegah data sensitif (seperti hashed_password) bocor ke
  respons API yang dikonsumsi oleh frontend atau pihak ketiga.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Payload untuk mendaftarkan Guru baru ke server lokal."""
    full_name: str = Field(..., min_length=3, max_length=150, json_schema_extra={"example": "Ibu Yuli Rahayu"})
    username: str = Field(..., min_length=4, max_length=80, json_schema_extra={"example": "yuli_sd12"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "rahasia123"})
    school_name: Optional[str] = Field(None, json_schema_extra={"example": "SD Negeri Dayeuhkolot 12"})
    school_region: Optional[str] = Field(None, json_schema_extra={"example": "Kab. Bandung, Jawa Barat"})


class UserLogin(BaseModel):
    """Payload untuk login Guru."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Data Guru yang aman dikembalikan ke FE (tanpa password)."""
    id: str
    full_name: str
    username: str
    school_name: Optional[str]
    school_region: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChildProfileCreate(BaseModel):
    """Payload untuk menambahkan profil siswa baru oleh Guru."""
    name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "Daniel Pratama"})
    age: Optional[int] = Field(None, ge=4, le=18, json_schema_extra={"example": 9})
    gender: Optional[str] = Field(None, json_schema_extra={"example": "L"})
    grade: Optional[str] = Field(None, json_schema_extra={"example": "Kelas 3 SD"})
    teacher_notes: Optional[str] = Field(None, json_schema_extra={"example": "Sering salah tulis huruf b dan d"})


class ChildProfileResponse(BaseModel):
    """Data profil anak yang dikembalikan ke FE."""
    id: str
    teacher_id: Optional[str]
    name: str
    age: Optional[int]
    gender: Optional[str]
    grade: Optional[str]
    current_level: int
    risk_score: float
    risk_level: str
    teacher_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
