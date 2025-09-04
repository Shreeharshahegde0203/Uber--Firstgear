from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_driver = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rides_as_rider = relationship("Ride", foreign_keys="Ride.rider_id", back_populates="rider")
    rides_as_driver = relationship("Ride", foreign_keys="Ride.driver_id", back_populates="driver")


class Ride(Base):
    __tablename__ = "rides"
    
    id = Column(Integer, primary_key=True, index=True)
    rider_id = Column(Integer, ForeignKey("users.id"))
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_location = Column(String)
    end_location = Column(String)
    status = Column(String, default="requested")  # requested, accepted, in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    fare = Column(Float, nullable=True)
    
    # Relationships
    rider = relationship("User", foreign_keys=[rider_id], back_populates="rides_as_rider")
    driver = relationship("User", foreign_keys=[driver_id], back_populates="rides_as_driver")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"))
    amount = Column(Float)
    status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ride = relationship("Ride")
