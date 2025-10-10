from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt

from ..db.database import get_db
from ..db.models import User
from ..core.schemas import UserResponse
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user: UserResponse
    message: str

@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and return their information
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return {
        "user": user,
        "message": "Login successful"
    }

@router.post("/register", response_model=UserResponse)
def register(user_data: dict, db: Session = Depends(get_db)):
    """
    Register a new user (rider or driver)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.get("email")) | (User.username == user_data.get("username"))
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.get("password").encode('utf-8'), bcrypt.gensalt())
    
    # Create new user
    new_user = User(
        username=user_data.get("username"),
        email=user_data.get("email"),
        hashed_password=hashed_password.decode('utf-8'),
        is_driver=user_data.get("is_driver", False),
        vehicle=user_data.get("vehicle"),
        availability=user_data.get("is_driver", False)  # Drivers start as available
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
