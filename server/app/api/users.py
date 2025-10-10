from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt

from ..db.database import get_db
from ..db.models import User
from ..core.schemas import UserCreate, UserResponse

router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Hash the password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password.decode('utf-8'),
        is_driver=user.is_driver
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return db_user

@router.put("/{user_id}/location", response_model=UserResponse)
def update_user_location(user_id: int, location_data: dict, db: Session = Depends(get_db)):
    """Update a user's current location (latitude and longitude)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update location
    db_user.latitude = location_data.get("latitude")
    db_user.longitude = location_data.get("longitude")
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.put("/{user_id}/availability", response_model=UserResponse)
def update_user_availability(user_id: int, availability_data: dict, db: Session = Depends(get_db)):
    """Toggle driver availability (online/offline)"""
    db_user = db.query(User).filter(User.id == user_id, User.is_driver == True).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Update availability
    db_user.availability = availability_data.get("availability", True)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user
