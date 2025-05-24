import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.consultation import generate_case, score_consultation
from app.db.load import load
from app.models.case import Case, ICE, BackgroundDetail, InformationDivulged, DoctorInfo
from app.schema.case import CreateCaseRequest, CaseDetails
from app.core.config import settings
from loguru import logger


router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("/generate_case", status_code=status.HTTP_200_OK) 
async def generate_case(db: Session = Depends(load)):
    """Generate a new patient case for consultation"""
    try:
        # case_data = generate_case()
        case_data = {
            "name": "John Doe",
            "age": 30,
            "presenting": "I have a headache",
            "context": "I have a headache"
        }
        
        # Store the case in the database
        new_case = Case(
            case_number=case_data["name"],
            patient_name=case_data["name"],
            patient_age=case_data["age"],
            presenting_complaint=case_data["presenting"],
            notes=case_data["context"]
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        
        doctor_info = DoctorInfo(
            case_id=new_case.id,
            name=case_data["name"],
            age=case_data["age"],
            past_medical_history="Patient reports occasional migraines since age 25",
            current_medication="Paracetamol as needed",
            context="Patient is a software engineer who works long hours on the computer"
        )
        db.add(doctor_info)
        db.commit()
        
        return case_data
    except Exception as e:
        error_detail = str(e)
        raise HTTPException(status_code=(
                e.status_code
                if hasattr(e, "status_code")
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "message": "Failed to generate case",
                "error": error_detail,
            },
        )


@router.post("/create_case", status_code=status.HTTP_201_CREATED, response_model=CaseDetails)  
async def create_case(request: CreateCaseRequest, db: Session = Depends(load)):
    """Create a new patient case with ICE entries, background details, and information divulged"""
    try:
        # Create the main case record
        new_case = Case(
            case_number=request.case_number,
            patient_name=request.patient_name,
            patient_age=request.patient_age,
            presenting_complaint=request.presenting_complaint,
            notes=request.notes
        )
        db.add(new_case)
        
        # Commit to get the new case ID
        db.commit()
        db.refresh(new_case)
        
        # Create ICE entries
        for ice_entry in request.ice_entries:
            ice = ICE(
                case_id=new_case.id,
                ice_type=ice_entry.ice_type,
                description=ice_entry.description
            )
            db.add(ice)
        
        # Create background details
        for bg_detail in request.background_details:
            detail = BackgroundDetail(
                case_id=new_case.id,
                detail=bg_detail.detail
            )
            db.add(detail)
        
        # Create information divulged entries
        for info_divulged in request.information_divulged:
            info = InformationDivulged(
                case_id=new_case.id,
                divulgence_type=info_divulged.divulgence_type,
                description=info_divulged.description
            )
            db.add(info)
            
        # Create doctor info if provided
        if request.doctor_info:
            doctor_info = DoctorInfo(
                case_id=new_case.id,
                name=request.doctor_info.name,
                age=request.doctor_info.age,
                past_medical_history=request.doctor_info.past_medical_history,
                current_medication=request.doctor_info.current_medication,
                context=request.doctor_info.context
            )
            db.add(doctor_info)
        
        db.commit()        
        db.refresh(new_case)
        
        return new_case
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        logger.exception(f"Error creating case: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", status_code=status.HTTP_200_OK)
async def get_cases(db: Session = Depends(load)):
    """Get all patient cases"""
    try:
        cases = db.query(Case).order_by(Case.created_at.desc()).all()
        
        result = []
        for case in cases:
            case_data = {
                "id": case.id,
                "case_number": case.case_number,
                "patient_name": case.patient_name,
                "patient_age": case.patient_age,
                "presenting_complaint": case.presenting_complaint,
                "notes": case.notes,
                "created_at": case.created_at.isoformat(),
            }
            
                
            result.append(case_data)
        
        return {"cases": result}
    except Exception as e:
        logger.error(f"Error retrieving cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{case_id}", status_code=status.HTTP_200_OK, response_model=CaseDetails)
async def get_case(case_id: str, db: Session = Depends(load)):
    """Get a specific patient case by ID with all related data"""
    try:
        case = db.query(Case).filter_by(id=case_id).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
            
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{case_id}/doctor_info", status_code=status.HTTP_200_OK)
async def get_doctor_info(case_id: str, db: Session = Depends(load)):
    """Get doctor information for a specific case"""
    try:
        doctor_info = db.query(DoctorInfo).filter_by(case_id=case_id).first()
        
        if not doctor_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor information for case {case_id} not found"
            )
            
        return {
            "id": doctor_info.id,
            "case_id": doctor_info.case_id,
            "name": doctor_info.name,
            "age": doctor_info.age,
            "past_medical_history": doctor_info.past_medical_history,
            "current_medication": doctor_info.current_medication,
            "context": doctor_info.context,
           
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving doctor info for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )