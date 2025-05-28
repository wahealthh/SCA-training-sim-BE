from sqlalchemy import Column, Integer, Text, ForeignKey, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base_model import BaseModel, Base


class ICEType(str, enum.Enum):
    IDEA = "IDEA"
    CONCERN = "CONCERN"
    EXPECTATION = "EXPECTATION"
    MIXED = "MIXED"


class DivulgenceType(str, enum.Enum):
    FREELY_DIVULGED = "FREELY_DIVULGED"
    SPECIFICALLY_ASKED = "SPECIFICALLY_ASKED"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Case(BaseModel, Base):
    """
    Case model for patient scenarios
    """
    __tablename__ = 'cases'
    
    case_number = Column(String(50), nullable=False, unique=True, index=True)
    patient_name = Column(String(255), nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(SQLAlchemyEnum(Gender), nullable=True)
    presenting_complaint = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    ice_entries = relationship("ICE", back_populates="case", cascade="all, delete-orphan")
    background_details = relationship("BackgroundDetail", back_populates="case", cascade="all, delete-orphan")
    information_divulged = relationship("InformationDivulged", back_populates="case", cascade="all, delete-orphan")
    consultations = relationship("Consultation", back_populates="case")
    doctor_info = relationship("DoctorInfo", back_populates="case", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Case(id={self.id}, case_number='{self.case_number}')>"


class DoctorInfo(BaseModel, Base):
    """
    Doctor information related to a case
    """
    __tablename__ = 'doctor_info'
    
    case_id = Column(String(36), ForeignKey('cases.id', ondelete='CASCADE'), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    past_medical_history = Column(Text, nullable=True)
    current_medication = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    
    case = relationship("Case", back_populates="doctor_info")
    
    def __repr__(self):
        return f"<DoctorInfo(id={self.id}, name='{self.name}')>"


class ICE(BaseModel, Base):
    """
    Ideas, Concerns, and Expectations related to a case
    """
    __tablename__ = 'ice'
    
    case_id = Column(String(36), ForeignKey('cases.id', ondelete='CASCADE'), nullable=False)
    ice_type = Column(SQLAlchemyEnum(ICEType), nullable=False)
    description = Column(Text, nullable=False)
    
    # 
    case = relationship("Case", back_populates="ice_entries")
    
    def __repr__(self):
        return f"<ICE(id={self.id}, type={self.ice_type})>"


class BackgroundDetail(BaseModel, Base):
    """
    Background information for a case
    """
    __tablename__ = 'background_details'
    
    case_id = Column(String(36), ForeignKey('cases.id', ondelete='CASCADE'), nullable=False)
    detail = Column(Text, nullable=False)
    
    case = relationship("Case", back_populates="background_details")
    
    def __repr__(self):
        return f"<BackgroundDetail(id={self.id})>"


class InformationDivulged(BaseModel, Base):
    """
    Information divulged by patient either freely or when specifically asked
    """
    __tablename__ = 'information_divulged'
    
    case_id = Column(String(36), ForeignKey('cases.id', ondelete='CASCADE'), nullable=False)
    divulgence_type = Column(SQLAlchemyEnum(DivulgenceType), nullable=False)
    description = Column(Text, nullable=False)
    
    case = relationship("Case", back_populates="information_divulged")
    
    def __repr__(self):
        return f"<InformationDivulged(id={self.id}, type={self.divulgence_type})>"