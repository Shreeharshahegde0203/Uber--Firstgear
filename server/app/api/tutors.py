"""
Tutor API Endpoints
Handles tutor registration, profile management, availability, and verification
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, validator

from ..db.database import get_db
from ..db.models import User, Tutor, TutorAvailability, TutorVerificationStatus

router = APIRouter(prefix="/api/tutors", tags=["Tutors"])


# ==================
# PYDANTIC SCHEMAS
# ==================

class TutorRegistrationRequest(BaseModel):
    user_id: int
    license_number: str
    license_expiry: str  # ISO format: "2026-12-31"
    years_experience: int
    bio: str
    specializations: List[str]  # ["beginner", "test_prep", "highway"]
    languages: List[str]  # ["english", "hindi", "kannada"]
    vehicle_available: bool
    vehicle_type: Optional[str] = None
    vehicle_registration: Optional[str] = None
    hourly_rate_own_vehicle: float
    hourly_rate_tutor_vehicle: float
    min_lesson_hours: float = 1.0
    
    @validator('years_experience')
    def validate_experience(cls, v):
        if v < 1:
            raise ValueError('Must have at least 1 year of experience')
        return v
    
    @validator('hourly_rate_own_vehicle', 'hourly_rate_tutor_vehicle')
    def validate_rates(cls, v):
        if v < 100 or v > 2000:
            raise ValueError('Hourly rate must be between ₹100 and ₹2000')
        return v


class TutorUpdateRequest(BaseModel):
    bio: Optional[str] = None
    specializations: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    vehicle_available: Optional[bool] = None
    vehicle_type: Optional[str] = None
    hourly_rate_own_vehicle: Optional[float] = None
    hourly_rate_tutor_vehicle: Optional[float] = None
    is_active: Optional[bool] = None


class AvailabilityRequest(BaseModel):
    date: str  # ISO format: "2025-10-20"
    start_time: str  # "09:00"
    end_time: str  # "18:00"
    is_recurring: bool = False
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday


class TutorResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    license_number: str
    years_experience: int
    bio: str
    specializations: List[str]
    languages: List[str]
    vehicle_available: bool
    vehicle_type: Optional[str]
    hourly_rate_own_vehicle: float
    hourly_rate_tutor_vehicle: float
    rating: float
    total_lessons: int
    verification_status: str
    is_active: bool
    
    class Config:
        from_attributes = True


# ==================
# API ENDPOINTS
# ==================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_tutor(request: TutorRegistrationRequest, db: Session = Depends(get_db)):
    """
    Register a new tutor profile
    """
    # Check if user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already a tutor
    existing_tutor = db.query(Tutor).filter(Tutor.user_id == request.user_id).first()
    if existing_tutor:
        raise HTTPException(status_code=400, detail="User is already registered as a tutor")
    
    # Check license uniqueness
    existing_license = db.query(Tutor).filter(Tutor.license_number == request.license_number).first()
    if existing_license:
        raise HTTPException(status_code=400, detail="License number already registered")
    
    # Create tutor profile
    tutor = Tutor(
        user_id=request.user_id,
        license_number=request.license_number,
        license_expiry=datetime.fromisoformat(request.license_expiry),
        years_experience=request.years_experience,
        bio=request.bio,
        specializations=",".join(request.specializations),
        languages=",".join(request.languages),
        vehicle_available=request.vehicle_available,
        vehicle_type=request.vehicle_type,
        vehicle_registration=request.vehicle_registration,
        hourly_rate_own_vehicle=request.hourly_rate_own_vehicle,
        hourly_rate_tutor_vehicle=request.hourly_rate_tutor_vehicle,
        min_lesson_hours=request.min_lesson_hours,
        # service_area_lat=request.service_area_lat,  # Temporarily disabled until migration
        # service_area_lng=request.service_area_lng,
        # service_radius_km=request.service_radius_km,
        verification_status=TutorVerificationStatus.PENDING.value
    )
    
    db.add(tutor)
    db.commit()
    db.refresh(tutor)
    
    return {
        "message": "Tutor registration successful. Verification pending.",
        "tutor_id": tutor.id,
        "verification_status": tutor.verification_status
    }


@router.get("/profile/{tutor_id}", response_model=TutorResponse)
async def get_tutor_profile(tutor_id: int, db: Session = Depends(get_db)):
    """
    Get tutor profile by ID
    """


@router.get("/user/{user_id}")
async def check_tutor_status(user_id: int, db: Session = Depends(get_db)):
    """
    Check if a user is registered as a tutor
    """
    tutor = db.query(Tutor).filter(Tutor.user_id == user_id).first()
    
    if not tutor:
        return {
            "is_tutor": False,
            "tutor": None
        }
    
    user = db.query(User).filter(User.id == tutor.user_id).first()
    
    return {
        "is_tutor": True,
        "tutor": {
            "id": tutor.id,
            "user_id": tutor.user_id,
            "username": user.username if user else "Unknown",
            "email": user.email if user else "",
            "license_number": tutor.license_number,
            "years_experience": tutor.years_experience,
            "bio": tutor.bio,
            "specializations": tutor.specializations.split(",") if tutor.specializations else [],
            "languages": tutor.languages.split(",") if tutor.languages else [],
            "vehicle_available": tutor.vehicle_available,
            "vehicle_type": tutor.vehicle_type,
            "hourly_rate_own_vehicle": tutor.hourly_rate_own_vehicle,
            "hourly_rate_tutor_vehicle": tutor.hourly_rate_tutor_vehicle,
            "rating": tutor.rating,
            "total_lessons": tutor.total_lessons,
            "verification_status": tutor.verification_status,
            "is_active": tutor.is_active
        }
    }


@router.get("/profile/{tutor_id}", response_model=TutorResponse)
async def get_tutor_profile(tutor_id: int, db: Session = Depends(get_db)):
    """
    Get tutor profile by ID
    """
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")
    
    user = db.query(User).filter(User.id == tutor.user_id).first()
    
    return {
        "id": tutor.id,
        "user_id": tutor.user_id,
        "username": user.username,
        "email": user.email,
        "license_number": tutor.license_number,
        "years_experience": tutor.years_experience,
        "bio": tutor.bio,
        "specializations": tutor.specializations.split(",") if tutor.specializations else [],
        "languages": tutor.languages.split(",") if tutor.languages else [],
        "vehicle_available": tutor.vehicle_available,
        "vehicle_type": tutor.vehicle_type,
        "hourly_rate_own_vehicle": tutor.hourly_rate_own_vehicle,
        "hourly_rate_tutor_vehicle": tutor.hourly_rate_tutor_vehicle,
        "rating": tutor.rating,
        "total_lessons": tutor.total_lessons,
        "verification_status": tutor.verification_status,
        "is_active": tutor.is_active
    }


@router.put("/profile/{tutor_id}")
async def update_tutor_profile(tutor_id: int, request: TutorUpdateRequest, db: Session = Depends(get_db)):
    """
    Update tutor profile
    """
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")
    
    # Update fields if provided
    if request.bio is not None:
        tutor.bio = request.bio
    if request.specializations is not None:
        tutor.specializations = ",".join(request.specializations)
    if request.languages is not None:
        tutor.languages = ",".join(request.languages)
    if request.vehicle_available is not None:
        tutor.vehicle_available = request.vehicle_available
    if request.vehicle_type is not None:
        tutor.vehicle_type = request.vehicle_type
    if request.hourly_rate_own_vehicle is not None:
        tutor.hourly_rate_own_vehicle = request.hourly_rate_own_vehicle
    if request.hourly_rate_tutor_vehicle is not None:
        tutor.hourly_rate_tutor_vehicle = request.hourly_rate_tutor_vehicle
    if request.is_active is not None:
        tutor.is_active = request.is_active
    
    tutor.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Profile updated successfully"}


@router.post("/availability/{tutor_id}")
async def add_availability(tutor_id: int, request: AvailabilityRequest, db: Session = Depends(get_db)):
    """
    Add tutor availability slots
    """
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")
    
    availability = TutorAvailability(
        tutor_id=tutor_id,
        date=datetime.fromisoformat(request.date),
        start_time=request.start_time,
        end_time=request.end_time,
        is_recurring=request.is_recurring,
        day_of_week=request.day_of_week
    )
    
    db.add(availability)
    db.commit()
    
    return {"message": "Availability added successfully"}


@router.get("/availability/{tutor_id}")
async def get_availability(tutor_id: int, date_from: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get tutor availability for date range
    """
    query = db.query(TutorAvailability).filter(TutorAvailability.tutor_id == tutor_id)
    
    if date_from:
        date_from_obj = datetime.fromisoformat(date_from)
        query = query.filter(TutorAvailability.date >= date_from_obj)
    
    availabilities = query.filter(TutorAvailability.is_available == True).all()
    
    return {
        "tutor_id": tutor_id,
        "slots": [
            {
                "id": av.id,
                "date": av.date.isoformat(),
                "start_time": av.start_time,
                "end_time": av.end_time,
                "is_booked": av.is_booked
            }
            for av in availabilities
        ]
    }


@router.get("/search")
async def search_tutors(
    lesson_type: Optional[str] = None,
    language: Optional[str] = None,
    vehicle_needed: bool = False,
    min_rating: float = 0.0,
    max_rate: float = 2000.0,
    db: Session = Depends(get_db)
):
    """
    Search for tutors with filters
    """
    query = db.query(Tutor).filter(
        Tutor.verification_status == TutorVerificationStatus.VERIFIED.value,
        Tutor.is_active == True,
        Tutor.rating >= min_rating
    )
    
    # Filter by lesson type specialization
    if lesson_type:
        query = query.filter(Tutor.specializations.contains(lesson_type))
    
    # Filter by language
    if language:
        query = query.filter(Tutor.languages.contains(language))
    
    # Filter by vehicle availability
    if vehicle_needed:
        query = query.filter(Tutor.vehicle_available == True)
        query = query.filter(Tutor.hourly_rate_tutor_vehicle <= max_rate)
    else:
        query = query.filter(Tutor.hourly_rate_own_vehicle <= max_rate)
    
    tutors = query.order_by(Tutor.rating.desc()).limit(20).all()
    
    results = []
    for tutor in tutors:
        user = db.query(User).filter(User.id == tutor.user_id).first()
        results.append({
            "id": tutor.id,
            "username": user.username,
            "years_experience": tutor.years_experience,
            "bio": tutor.bio[:100] + "..." if len(tutor.bio) > 100 else tutor.bio,
            "specializations": tutor.specializations.split(",") if tutor.specializations else [],
            "languages": tutor.languages.split(",") if tutor.languages else [],
            "vehicle_available": tutor.vehicle_available,
            "hourly_rate_own_vehicle": tutor.hourly_rate_own_vehicle,
            "hourly_rate_tutor_vehicle": tutor.hourly_rate_tutor_vehicle,
            "rating": tutor.rating,
            "total_lessons": tutor.total_lessons
        })
    
    return {"tutors": results, "count": len(results)}


@router.get("/stats/{tutor_id}")
async def get_tutor_stats(tutor_id: int, db: Session = Depends(get_db)):
    """
    Get tutor statistics and performance metrics
    """
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")
    
    from ..db.models import LessonBooking, LessonStatus
    
    # Get completed lessons count
    completed_lessons = db.query(LessonBooking).filter(
        LessonBooking.tutor_id == tutor_id,
        LessonBooking.status == LessonStatus.COMPLETED.value
    ).count()
    
    # Get average rating from students
    avg_rating_result = db.query(
        db.func.avg(LessonBooking.student_rating)
    ).filter(
        LessonBooking.tutor_id == tutor_id,
        LessonBooking.student_rating.isnot(None)
    ).scalar()
    
    return {
        "tutor_id": tutor_id,
        "total_lessons": tutor.total_lessons,
        "completed_lessons": completed_lessons,
        "rating": tutor.rating,
        "average_student_rating": float(avg_rating_result) if avg_rating_result else 5.0,
        "total_earnings": tutor.total_earnings,
        "success_rate": tutor.success_rate,
        "verification_status": tutor.verification_status
    }
