from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from ..db.database import get_db
from ..db.models import Ride, User
from ..core.schemas import RideCreate, RideResponse
from ..services.matching_engine import matching_engine

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request models for new endpoints
class DriverActionRequest(BaseModel):
    driver_id: int


class AcceptanceResponse(BaseModel):
    success: bool
    message: str
    ride: Optional[RideResponse] = None

@router.post("/", response_model=RideResponse)
def create_ride(ride: RideCreate, rider_id: int, db: Session = Depends(get_db)):
    # Check if rider exists
    rider = db.query(User).filter(User.id == rider_id, User.is_driver == False).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Create new ride
    db_ride = Ride(
        rider_id=rider_id,
        start_location=ride.start_location,
        end_location=ride.end_location,
        status="requested"
    )
    
    db.add(db_ride)
    db.commit()
    db.refresh(db_ride)
    
    return db_ride

@router.get("/{ride_id}", response_model=RideResponse)
def get_ride(ride_id: int, db: Session = Depends(get_db)):
    db_ride = db.query(Ride).filter(Ride.id == ride_id).first()
    
    if not db_ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Attach rider and driver information for mutual visibility
    rider = db.query(User).filter(User.id == db_ride.rider_id).first()
    driver = db.query(User).filter(User.id == db_ride.driver_id).first() if db_ride.driver_id else None
    db_ride.rider = rider
    db_ride.driver = driver
    
    return db_ride

@router.put("/{ride_id}/accept")
async def accept_ride_offer(
    ride_id: int,
    driver_data: DriverActionRequest,
    db: Session = Depends(get_db)
):
    """
    Driver accepts a ride offer (new system with timeout validation)
    
    Edge cases handled:
    - Offer expired
    - Wrong driver
    - Ride already accepted by someone else
    - Ride cancelled
    - Concurrent acceptance attempts
    """
    success, message = await matching_engine.handle_driver_accept(
        db, ride_id, driver_data.driver_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Fetch updated ride
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    
    # Attach rider and driver details
    rider = db.query(User).filter(User.id == ride.rider_id).first()
    driver = db.query(User).filter(User.id == ride.driver_id).first() if ride.driver_id else None
    ride.rider = rider
    ride.driver = driver
    
    return {
        "success": True,
        "message": message,
        "ride": ride
    }


@router.put("/{ride_id}/decline")
async def decline_ride_offer(
    ride_id: int,
    driver_data: DriverActionRequest,
    db: Session = Depends(get_db)
):
    """
    Driver declines a ride offer
    
    Edge cases handled:
    - Offer expired
    - Wrong driver
    - Ride already accepted/cancelled
    """
    success, message = await matching_engine.handle_driver_decline(
        db, ride_id, driver_data.driver_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }


@router.put("/{ride_id}/cancel")
def cancel_ride(
    ride_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a ride (can be called by rider)
    
    Edge cases handled:
    - Ride not found
    - Ride already completed
    - Ride currently in progress
    """
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Can only cancel if not yet in progress or completed
    if ride.status in ["completed", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel ride in {ride.status} state"
        )
    
    ride.status = "cancelled"
    ride.cancelled_at = datetime.utcnow()
    
    # If driver was assigned, free them up
    if ride.driver_id:
        driver = db.query(User).filter(User.id == ride.driver_id).first()
        if driver:
            driver.availability = True
    
    db.commit()
    db.refresh(ride)
    
    return {
        "success": True,
        "message": "Ride cancelled successfully",
        "ride": ride
    }

@router.put("/{ride_id}/complete", response_model=RideResponse)
def complete_ride(ride_id: int, fare: float = 25.0, db: Session = Depends(get_db)):
    """
    Complete a ride and free up the driver
    
    Edge cases handled:
    - Ride not found
    - Invalid status transition
    - Driver not found (shouldn't happen but defensive)
    """
    # Check if ride exists and is in correct status
    db_ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not db_ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    if db_ride.status not in ["accepted", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ride cannot be completed (current status: {db_ride.status})"
        )
    
    # Update ride
    db_ride.status = "completed"
    db_ride.completed_at = datetime.utcnow()
    db_ride.fare = fare
    
    # Free up the driver
    if db_ride.driver_id:
        driver = db.query(User).filter(User.id == db_ride.driver_id).first()
        if driver:
            driver.availability = True
            logger.info(f"✅ Driver #{driver.id} is now available again")
    
    db.commit()
    db.refresh(db_ride)
    
    return db_ride


@router.put("/{ride_id}/start")
def start_ride(ride_id: int, db: Session = Depends(get_db)):
    """
    Mark ride as in_progress (driver picked up rider)
    
    Edge cases handled:
    - Ride not accepted yet
    - Ride already completed/cancelled
    """
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    if ride.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ride must be accepted before starting (current: {ride.status})"
        )
    
    ride.status = "in_progress"
    db.commit()
    db.refresh(ride)
    
    return {
        "id": ride.id,
        "rider_id": ride.rider_id,
        "driver_id": ride.driver_id,
        "start_location": ride.start_location,
        "end_location": ride.end_location,
        "status": ride.status,
        "fare": ride.fare,
        "created_at": ride.created_at.isoformat() if ride.created_at else None
    }

@router.get("/", response_model=List[RideResponse])
def list_rides(status: Optional[str] = None, rider_id: Optional[int] = None, driver_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Ride)
    
    if status:
        query = query.filter(Ride.status == status)
    
    if rider_id:
        query = query.filter(Ride.rider_id == rider_id)
    
    if driver_id:
        query = query.filter(Ride.driver_id == driver_id)
    
    return query.all()
