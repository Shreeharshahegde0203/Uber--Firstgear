from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..db.database import get_db
from ..db.models import Ride, User
from ..core.schemas import RideCreate, RideResponse

router = APIRouter()

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

@router.put("/{ride_id}/accept", response_model=RideResponse)
def accept_ride(ride_id: int, driver_data: dict, db: Session = Depends(get_db)):
    # Extract driver_id from request body
    driver_id = driver_data.get("driver_id")
    if not driver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="driver_id is required"
        )
    
    # Check if driver exists
    driver = db.query(User).filter(User.id == driver_id, User.is_driver == True).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Check if ride exists and is in "requested" status
    db_ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not db_ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    if db_ride.status != "requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ride cannot be accepted (current status: {db_ride.status})"
        )
    
    # Update ride
    db_ride.driver_id = driver_id
    db_ride.status = "accepted"
    
    db.commit()
    db.refresh(db_ride)
    # Attach full rider and driver details for mutual visibility
    rider = db.query(User).filter(User.id == db_ride.rider_id).first()
    driver = db.query(User).filter(User.id == db_ride.driver_id).first() if db_ride.driver_id else None
    db_ride.rider = rider
    db_ride.driver = driver
    return db_ride

@router.put("/{ride_id}/complete", response_model=RideResponse)
def complete_ride(ride_id: int, fare: float, db: Session = Depends(get_db)):
    # Check if ride exists and is in "accepted" or "in_progress" status
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
    
    db.commit()
    db.refresh(db_ride)
    
    return db_ride

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
