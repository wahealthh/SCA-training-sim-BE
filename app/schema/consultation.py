from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.models.consultation import ICEType, DivulgenceType


# Input models for creating entries

class ICECreate(BaseModel):
    ice_type: ICEType
    description: str


class BackgroundDetailCreate(BaseModel):
    detail: str


class InformationDivulgedCreate(BaseModel):
    divulgence_type: DivulgenceType
    description: str


class DoctorInfoCreate(BaseModel):
    name: str
    age: Optional[int] = None
    past_medical_history: Optional[str] = None
    current_medication: Optional[str] = None
    context: Optional[str] = None


class CreateCaseRequest(BaseModel):
    case_number: str
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    presenting_complaint: str
    notes: Optional[str] = None
    ice_entries: List[ICECreate] = []
    background_details: List[BackgroundDetailCreate] = []
    information_divulged: List[InformationDivulgedCreate] = []
    doctor_info: Optional[DoctorInfoCreate] = None

    class Config:
        orm_mode = True


# Response models including IDs for created entries

class ICEResponse(ICECreate):
    id: str
    case_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BackgroundDetailResponse(BackgroundDetailCreate):
    id: str
    case_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class InformationDivulgedResponse(InformationDivulgedCreate):
    id: str
    case_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DoctorInfoResponse(DoctorInfoCreate):
    id: str
    case_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CaseResponse(BaseModel):
    id: str
    case_number: str
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    presenting_complaint: str
    notes: Optional[str] = None
    ice_entries: List[ICEResponse] = []
    background_details: List[BackgroundDetailResponse] = []
    information_divulged: List[InformationDivulgedResponse] = []
    doctor_info: Optional[DoctorInfoResponse] = None

    class Config:
        orm_mode = True


# Keep existing models for other functionality

class CaseDetails(BaseModel):
    case_number: str
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    presenting_complaint: str
    notes: Optional[str] = None
    # Note: We don't include the related entries (ice, background, etc.) here as they're not 
    # directly needed for scoring. If needed, they can be fetched from the database separately.


class ScoreRequest(BaseModel):
    transcript: str
    case_details: CaseDetails
    user_id: str


class CommentRequest(BaseModel):
    comment: str
    user_id: str

    class Config:
        orm_mode = True