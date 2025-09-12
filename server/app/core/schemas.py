from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    email: str
    is_driver: bool = False

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    vehicle: Optional[str] = None
    rating: Optional[float] = None
    class Config:
        orm_mode = True

# Ping-Pong schemas
class PingRequest(BaseModel):
    data: str

class PongResponse(BaseModel):
    message: str

# Ride schemas
class RideCreate(BaseModel):
    start_location: str
    end_location: str

class RideResponse(BaseModel):
    id: int
    rider_id: int
    driver_id: Optional[int] = None
    start_location: str
    end_location: str
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    fare: Optional[float] = None
    rider: Optional[UserResponse] = None
    driver: Optional[UserResponse] = None
    class Config:
        orm_mode = True

# Payment schemas
class PaymentResponse(BaseModel):
    id: int
    ride_id: int
    amount: float
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True
