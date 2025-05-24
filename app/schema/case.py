from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.models.case import ICEType, DivulgenceType


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


class CaseDetails(BaseModel):
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


