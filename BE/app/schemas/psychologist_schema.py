from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PsychologistCreate(BaseModel):
    full_name: str
    username: str
    password: str
    license_number: str
    clinic_name: Optional[str] = None

class PsychologistLogin(BaseModel):
    username: str
    password: str

class PsychologistResponse(BaseModel):
    id: str
    full_name: str
    username: str
    license_number: str
    clinic_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class RecommendationCreate(BaseModel):
    clinical_notes: str
    medical_recommendations: str

class RecommendationResponse(BaseModel):
    id: str
    child_id: str
    psychologist_id: str
    clinical_notes: str
    medical_recommendations: str
    created_at: datetime
    psychologist_name: Optional[str] = None

    class Config:
        from_attributes = True

class StudentListResponse(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    grade: Optional[str] = None
    current_level: int
    risk_score: float
    risk_level: str
    has_medical_recommendation: bool
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True
