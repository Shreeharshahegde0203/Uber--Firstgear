from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, ARRAY, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

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
    
    # Gamification
    coins = Column(Integer, default=0)
    last_quiz_date = Column(DateTime, nullable=True)

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


# ==========================
# TUTOR BOOKING SYSTEM MODELS
# ==========================

class TutorVerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class LessonType(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    TEST_PREP = "test_prep"
    HIGHWAY = "highway"
    PARKING = "parking"
    DEFENSIVE = "defensive_driving"


class LessonStatus(str, enum.Enum):
    REQUESTED = "requested"
    BIDDING_OPEN = "bidding_open"
    TUTOR_SELECTED = "tutor_selected"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BidStatus(str, enum.Enum):
    ACTIVE = "active"
    SELECTED = "selected"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Tutor(Base):
    __tablename__ = "tutors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Verification & credentials
    license_number = Column(String(50), unique=True)
    license_expiry = Column(DateTime)
    years_experience = Column(Integer)
    bio = Column(Text)
    
    # Specializations (stored as PostgreSQL ARRAY or comma-separated string)
    specializations = Column(String, nullable=True)  # e.g., "beginner,test_prep,highway"
    languages = Column(String, nullable=True)  # e.g., "english,hindi,kannada"
    
    # Vehicle information
    vehicle_available = Column(Boolean, default=False)
    vehicle_type = Column(String(50), nullable=True)  # e.g., "Manual Sedan", "Automatic SUV"
    vehicle_registration = Column(String(50), nullable=True)
    
    # Pricing
    hourly_rate_own_vehicle = Column(Float)  # When student brings vehicle
    hourly_rate_tutor_vehicle = Column(Float)  # When tutor provides vehicle
    min_lesson_hours = Column(Float, default=1.0)
    
    # Ratings & stats
    rating = Column(Float, default=5.0)
    total_lessons = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    success_rate = Column(Float, default=100.0)  # % of students who passed
    
    # Verification status
    verification_status = Column(String, default=TutorVerificationStatus.PENDING.value)
    verified_at = Column(DateTime, nullable=True)
    
    # Profile
    profile_photo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", backref="tutor_profile")
    availabilities = relationship("TutorAvailability", back_populates="tutor", cascade="all, delete-orphan")
    bids = relationship("LessonBid", back_populates="tutor", cascade="all, delete-orphan")
    lessons = relationship("LessonBooking", foreign_keys="LessonBooking.tutor_id", back_populates="tutor")


class TutorAvailability(Base):
    __tablename__ = "tutor_availabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey("tutors.id"))
    
    # Date and time
    date = Column(DateTime, index=True)
    start_time = Column(String(5))  # e.g., "09:00"
    end_time = Column(String(5))    # e.g., "18:00"
    
    # Status
    is_available = Column(Boolean, default=True)
    is_booked = Column(Boolean, default=False)
    booking_id = Column(Integer, ForeignKey("lesson_bookings.id"), nullable=True)
    
    # Recurrence (optional - for recurring availability)
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    is_recurring = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tutor = relationship("Tutor", back_populates="availabilities")


class LessonBooking(Base):
    __tablename__ = "lesson_bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    tutor_id = Column(Integer, ForeignKey("tutors.id"), nullable=True)
    
    # Lesson details
    lesson_date = Column(DateTime, index=True)
    start_time = Column(String(5))  # e.g., "10:00"
    end_time = Column(String(5))    # e.g., "12:00"
    duration_hours = Column(Float)  # e.g., 2.0
    
    # Location
    pickup_location = Column(String)
    pickup_lat = Column(Float)
    pickup_lng = Column(Float)
    
    # Type & preferences
    lesson_type = Column(String, default=LessonType.BEGINNER.value)
    student_vehicle = Column(Boolean, default=False)  # True if student brings vehicle
    special_requirements = Column(Text, nullable=True)
    
    # Bidding process
    status = Column(String, default=LessonStatus.REQUESTED.value, index=True)
    bidding_opens_at = Column(DateTime, default=datetime.utcnow)
    bidding_closes_at = Column(DateTime)  # 30 minutes from creation
    total_bids = Column(Integer, default=0)
    
    # Financial
    final_price = Column(Float, nullable=True)
    platform_fee = Column(Float, nullable=True)  # 15% of final_price
    tutor_payout = Column(Float, nullable=True)  # 85% of final_price
    payment_status = Column(String, default="pending")  # pending, completed, refunded
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Feedback
    student_rating = Column(Float, nullable=True)
    student_feedback = Column(Text, nullable=True)
    tutor_rating = Column(Float, nullable=True)
    tutor_feedback = Column(Text, nullable=True)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id], backref="lesson_bookings")
    tutor = relationship("Tutor", foreign_keys=[tutor_id], back_populates="lessons")
    bids = relationship("LessonBid", back_populates="booking", cascade="all, delete-orphan")
    progress = relationship("LessonProgress", back_populates="booking", uselist=False, cascade="all, delete-orphan")


class LessonBid(Base):
    __tablename__ = "lesson_bids"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("lesson_bookings.id"), index=True)
    tutor_id = Column(Integer, ForeignKey("tutors.id"), index=True)
    
    # Bid details
    bid_amount_per_hour = Column(Float)
    total_bid_amount = Column(Float)  # bid_amount_per_hour * duration_hours
    
    # Tutor message
    tutor_message = Column(Text, nullable=True)  # Optional pitch from tutor
    estimated_duration = Column(Float, nullable=True)  # Tutor's estimate if different
    
    # Status & ranking
    bid_status = Column(String, default=BidStatus.ACTIVE.value, index=True)
    bid_rank = Column(Integer, nullable=True)  # 1-10 for top bids shown to student
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    selected_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)
    
    # Relationships
    booking = relationship("LessonBooking", back_populates="bids")
    tutor = relationship("Tutor", back_populates="bids")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("lesson_bookings.id"), unique=True)
    
    # Skills tracking
    steering_control = Column(Integer, default=0)  # 0-100
    gear_shifting = Column(Integer, default=0)
    braking = Column(Integer, default=0)
    parking = Column(Integer, default=0)
    traffic_awareness = Column(Integer, default=0)
    confidence_level = Column(Integer, default=0)
    
    # Notes
    tutor_notes = Column(Text, nullable=True)
    areas_to_improve = Column(Text, nullable=True)
    next_lesson_focus = Column(Text, nullable=True)
    
    # Milestones
    can_start_vehicle = Column(Boolean, default=False)
    can_drive_straight = Column(Boolean, default=False)
    can_turn_corners = Column(Boolean, default=False)
    can_parallel_park = Column(Boolean, default=False)
    can_handle_traffic = Column(Boolean, default=False)
    ready_for_test = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking = relationship("LessonBooking", back_populates="progress")

