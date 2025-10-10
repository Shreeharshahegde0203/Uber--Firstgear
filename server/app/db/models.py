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
    availability = Column(Boolean, default=True)  # For drivers: online/offline status
    created_at = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    vehicle = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    # Relationships
    rides_as_rider = relationship("Ride", foreign_keys="Ride.rider_id", back_populates="rider")
    rides_as_driver = relationship("Ride", foreign_keys="Ride.driver_id", back_populates="driver")


class Ride(Base):
    __tablename__ = "rides"
    
    id = Column(Integer, primary_key=True, index=True)
    rider_id = Column(Integer, ForeignKey("users.id"))
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_location = Column(String)
    start_lat = Column(Float, nullable=True)
    start_lng = Column(Float, nullable=True)
    end_location = Column(String)
    end_lat = Column(Float, nullable=True)
    end_lng = Column(Float, nullable=True)
    
    # Enhanced status system for offer flow
    # Possible values: requested, offering, accepted, declined, expired, in_progress, completed, cancelled
    status = Column(String, default="requested", index=True)
    
    # Offer tracking fields
    offered_to_driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Current driver being offered
    offered_at = Column(DateTime, nullable=True)  # When offer was made
    expires_at = Column(DateTime, nullable=True)  # When offer expires (20 sec from offered_at)
    offer_attempts = Column(Integer, default=0)  # Number of drivers offered to
    declined_driver_ids = Column(String, nullable=True)  # Comma-separated list of driver IDs who declined
    
    # NEW: One-offer-per-driver tracking
    current_offer_driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Driver currently viewing offer
    offer_expires_at = Column(DateTime, nullable=True)  # When current offer expires (for queue management)
    cancellation_reason = Column(String(100), nullable=True)  # Why ride was cancelled
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
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
