"""
Lesson Booking API Endpoints
Handles lesson requests, bidding process, tutor selection, and lesson lifecycle
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, validator
import math

from ..db.database import get_db
from ..db.models import (
    User, Tutor, LessonBooking, LessonBid, LessonProgress,
    LessonStatus, BidStatus, LessonType
)

router = APIRouter(prefix="/api/lessons", tags=["Lessons"])

# Global reference to WebSocket manager (will be set in main.py)
websocket_manager = None

def set_websocket_manager(manager):
    """Set the WebSocket manager for notifications"""
    global websocket_manager
    websocket_manager = manager


# ==================
# PYDANTIC SCHEMAS
# ==================

class LessonRequest(BaseModel):
    student_id: int
    lesson_date: str  # ISO format: "2025-10-20"
    start_time: str   # "10:00"
    end_time: str     # "12:00"
    pickup_location: str
    pickup_lat: float
    pickup_lng: float
    lesson_type: str  # "beginner", "test_prep", etc.
    student_vehicle: bool = False
    special_requirements: Optional[str] = None
    
    @validator('lesson_type')
    def validate_lesson_type(cls, v):
        valid_types = [t.value for t in LessonType]
        if v not in valid_types:
            raise ValueError(f'Lesson type must be one of: {", ".join(valid_types)}')
        return v


class BidRequest(BaseModel):
    tutor_id: int
    booking_id: int
    bid_amount_per_hour: float
    tutor_message: Optional[str] = None
    
    @validator('bid_amount_per_hour')
    def validate_bid_amount(cls, v):
        if v < 50 or v > 2000:
            raise ValueError('Bid amount must be between ₹50 and ₹2000 per hour')
        return v


class SelectTutorRequest(BaseModel):
    booking_id: int
    selected_bid_id: int


class TutorAcceptRequest(BaseModel):
    booking_id: int
    tutor_id: int
    accept: bool  # True to accept, False to reject
    reject_reason: Optional[str] = None


class RatingRequest(BaseModel):
    booking_id: int
    rating: float
    feedback: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


# ==================
# HELPER FUNCTIONS
# ==================

def calculate_duration_hours(start_time: str, end_time: str) -> float:
    """Calculate duration in hours from time strings"""
    from datetime import datetime
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    duration = (end - start).seconds / 3600
    return duration


def calculate_platform_fee(amount: float) -> float:
    """Calculate 15% platform fee"""
    return round(amount * 0.15, 2)


def calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def get_max_radius_km(minutes_elapsed: int) -> float:
    """Calculate max search radius based on time elapsed since booking created"""
    # Start with 5km, increase by 2km every 5 minutes
    base_radius = 5.0
    increment_per_5min = 2.0
    
    increments = minutes_elapsed // 5
    return base_radius + (increments * increment_per_5min)


async def notify_nearby_tutors(booking_id: int, db: Session):
    """Notify tutors within expanding radius about new lesson booking, prioritizing nearest tutors first"""
    if not websocket_manager:
        return
    
    booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
    if not booking:
        return
    
    # Calculate time elapsed
    minutes_elapsed = (datetime.utcnow() - booking.created_at).seconds // 60
    max_radius = get_max_radius_km(minutes_elapsed)
    
    # Get all verified and active tutors
    tutors = db.query(Tutor).filter(
        Tutor.verification_status == "verified",
        Tutor.is_active == True
    ).all()
    
    # Build list of tutors with distances
    tutors_with_distance = []
    for tutor in tutors:
        # Use user's last known location for distance calculation (if available)
        user = db.query(User).filter(User.id == tutor.user_id).first()
        if user and user.latitude and user.longitude:
            distance_km = calculate_distance_km(
                user.latitude, user.longitude,
                booking.pickup_lat, booking.pickup_lng
            )
            
            # Skip if beyond max radius
            if distance_km > max_radius:
                continue
            
            tutors_with_distance.append({
                'tutor': tutor,
                'user': user,
                'distance_km': distance_km
            })
        else:
            # No location available - add with large distance so they're notified last
            tutors_with_distance.append({
                'tutor': tutor,
                'user': user,
                'distance_km': 999  # Put at end of list
            })
    
    # Sort by distance (nearest first)
    tutors_with_distance.sort(key=lambda x: x['distance_km'])
    
    notified_count = 0
    for item in tutors_with_distance:
        tutor = item['tutor']
        user = item['user']
        distance_km = item['distance_km'] if item['distance_km'] < 999 else 0
        
        # Send notification
        notification = {
            "type": "new_lesson_request",
            "booking_id": booking.id,
            "lesson_type": booking.lesson_type,
            "lesson_date": booking.lesson_date.isoformat(),
            "start_time": booking.start_time,
            "duration_hours": booking.duration_hours,
            "pickup_location": booking.pickup_location,
            "pickup_lat": booking.pickup_lat,
            "pickup_lng": booking.pickup_lng,
            "student_vehicle": booking.student_vehicle,
            "bidding_closes_at": booking.bidding_closes_at.isoformat(),
            "distance_km": round(distance_km, 2) if distance_km else 0,
            "max_radius_km": max_radius
        }
        
        await websocket_manager.send_to_user(tutor.user_id, notification)
        notified_count += 1
    
    return notified_count


def update_bid_rankings(booking_id: int, db: Session):
    """Update bid rankings (top 10 lowest bids get ranks 1-10)"""
    bids = db.query(LessonBid).filter(
        LessonBid.booking_id == booking_id,
        LessonBid.bid_status == BidStatus.ACTIVE.value
    ).order_by(LessonBid.total_bid_amount.asc()).all()
    
    # Assign ranks to top 10
    for i, bid in enumerate(bids[:10]):
        bid.bid_rank = i + 1
    
    # Remove ranks from others
    for bid in bids[10:]:
        bid.bid_rank = None
    
    db.commit()


# ==================
# API ENDPOINTS
# ==================

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_lesson(request: LessonRequest, db: Session = Depends(get_db)):
    """
    Student requests a new lesson - opens bidding window
    """
    # Verify student exists
    student = db.query(User).filter(User.id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Calculate duration
    duration = calculate_duration_hours(request.start_time, request.end_time)
    if duration < 0.5 or duration > 8:
        raise HTTPException(status_code=400, detail="Lesson duration must be between 0.5 and 8 hours")
    
    # Parse lesson date
    lesson_date = datetime.fromisoformat(request.lesson_date)
    if lesson_date < datetime.now():
        raise HTTPException(status_code=400, detail="Lesson date must be in the future")
    
    # Create lesson booking
    booking = LessonBooking(
        student_id=request.student_id,
        lesson_date=lesson_date,
        start_time=request.start_time,
        end_time=request.end_time,
        duration_hours=duration,
        pickup_location=request.pickup_location,
        pickup_lat=request.pickup_lat,
        pickup_lng=request.pickup_lng,
        lesson_type=request.lesson_type,
        student_vehicle=request.student_vehicle,
        special_requirements=request.special_requirements,
        status=LessonStatus.BIDDING_OPEN.value,
        bidding_opens_at=datetime.utcnow(),
        bidding_closes_at=datetime.utcnow() + timedelta(minutes=15)  # 15-minute bidding window
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    # Trigger notification to nearby tutors
    await notify_nearby_tutors(booking.id, db)
    
    return {
        "message": "Lesson request created successfully. Bidding is now open!",
        "booking_id": booking.id,
        "bidding_closes_at": booking.bidding_closes_at.isoformat(),
        "duration_hours": duration
    }


@router.get("/available")
async def get_available_lessons(
    tutor_id: Optional[int] = None,
    tutor_lat: Optional[float] = None,
    tutor_lng: Optional[float] = None,
    max_distance_km: float = 50.0,
    db: Session = Depends(get_db)
):
    """
    Get all available lesson bookings that are open for bidding
    Optionally filter by tutor location
    """
    # Get all open bookings
    current_time = datetime.utcnow()
    bookings = db.query(LessonBooking).filter(
        LessonBooking.status == LessonStatus.BIDDING_OPEN.value,
        LessonBooking.bidding_closes_at > current_time
    ).order_by(LessonBooking.created_at.desc()).all()
    
    results = []
    for booking in bookings:
        # Calculate distance if tutor location provided
        distance_km = None
        if tutor_lat is not None and tutor_lng is not None:
            distance_km = calculate_distance_km(
                tutor_lat, tutor_lng,
                booking.pickup_lat, booking.pickup_lng
            )
            
            # Skip if beyond max distance
            if distance_km > max_distance_km:
                continue
        
        # Calculate time elapsed and max radius
        minutes_elapsed = (current_time - booking.created_at).seconds // 60
        max_radius = get_max_radius_km(minutes_elapsed)
        
        # Check if tutor already bid on this
        already_bid = False
        if tutor_id:
            existing_bid = db.query(LessonBid).filter(
                LessonBid.booking_id == booking.id,
                LessonBid.tutor_id == tutor_id,
                LessonBid.bid_status == BidStatus.ACTIVE.value
            ).first()
            already_bid = existing_bid is not None
        
        # Get student info
        student = db.query(User).filter(User.id == booking.student_id).first()
        
        results.append({
            "booking_id": booking.id,
            "student_name": student.username if student else "Unknown",
            "lesson_date": booking.lesson_date.isoformat(),
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_hours": booking.duration_hours,
            "lesson_type": booking.lesson_type,
            "pickup_location": booking.pickup_location,
            "pickup_lat": booking.pickup_lat,
            "pickup_lng": booking.pickup_lng,
            "student_vehicle": booking.student_vehicle,
            "special_requirements": booking.special_requirements,
            "total_bids": booking.total_bids,
            "bidding_closes_at": booking.bidding_closes_at.isoformat(),
            "time_remaining_minutes": int((booking.bidding_closes_at - current_time).seconds / 60),
            "distance_km": round(distance_km, 2) if distance_km else None,
            "max_radius_km": max_radius,
            "already_bid": already_bid,
            "created_at": booking.created_at.isoformat()
        })
    
    return {
        "available_lessons": results,
        "count": len(results),
        "current_time": current_time.isoformat()
    }


@router.post("/bid")
async def place_bid(request: BidRequest, db: Session = Depends(get_db)):
    """
    Tutor places a bid on a lesson booking
    """
    print(f"🎯 BID REQUEST RECEIVED: tutor_id={request.tutor_id}, booking_id={request.booking_id}, amount={request.bid_amount_per_hour}")
    
    # Verify tutor exists and is verified
    tutor = db.query(Tutor).filter(Tutor.id == request.tutor_id).first()
    if not tutor:
        print(f"❌ Tutor {request.tutor_id} not found")
        raise HTTPException(status_code=404, detail="Tutor not found")
    # Allow both verified and pending tutors to bid (for testing/demo)
    if tutor.verification_status not in ["verified", "pending"]:
        print(f"❌ Tutor {request.tutor_id} not active: {tutor.verification_status}")
        raise HTTPException(status_code=403, detail="Tutor account is not active")
    
    # Verify booking exists and is open for bidding
    booking = db.query(LessonBooking).filter(LessonBooking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != LessonStatus.BIDDING_OPEN.value:
        raise HTTPException(status_code=400, detail="Bidding is closed for this lesson")
    if datetime.utcnow() > booking.bidding_closes_at:
        raise HTTPException(status_code=400, detail="Bidding window has expired")
    
    # Check if tutor already bid
    existing_bid = db.query(LessonBid).filter(
        LessonBid.booking_id == request.booking_id,
        LessonBid.tutor_id == request.tutor_id,
        LessonBid.bid_status == BidStatus.ACTIVE.value
    ).first()
    if existing_bid:
        raise HTTPException(status_code=400, detail="You have already placed a bid. Update or withdraw it first.")
    
    # Calculate total bid amount
    total_bid = round(request.bid_amount_per_hour * booking.duration_hours, 2)
    
    # Create bid
    bid = LessonBid(
        booking_id=request.booking_id,
        tutor_id=request.tutor_id,
        bid_amount_per_hour=request.bid_amount_per_hour,
        total_bid_amount=total_bid,
        tutor_message=request.tutor_message,
        bid_status=BidStatus.ACTIVE.value
    )
    
    db.add(bid)
    booking.total_bids += 1
    db.commit()
    db.refresh(bid)
    
    # Update rankings
    update_bid_rankings(request.booking_id, db)
    
    # Get tutor info for notification
    tutor_user = db.query(User).filter(User.id == tutor.user_id).first()
    
    # Send notification to student about new bid
    if websocket_manager:
        notification = {
            "type": "new_bid_received",
            "booking_id": booking.id,
            "bid_id": bid.id,
            "tutor_name": tutor_user.username if tutor_user else "Instructor",
            "tutor_rating": tutor.rating,
            "bid_amount": total_bid,
            "total_bids": booking.total_bids,
            "message": f"New bid of ₹{total_bid} received from {tutor_user.username if tutor_user else 'an instructor'}"
        }
        await websocket_manager.send_to_user(booking.student_id, notification)
    
    print(f"✅ BID PLACED: bid_id={bid.id}, total={total_bid}, rank={bid.bid_rank}")
    
    response_data = {
        "message": "Bid placed successfully!",
        "bid_id": bid.id,
        "total_bid_amount": total_bid,
        "bid_rank": bid.bid_rank if bid.bid_rank else "Not in top 10"
    }
    print(f"📤 SENDING RESPONSE: {response_data}")
    
    return response_data


@router.get("/bids/{booking_id}")
async def get_lesson_bids(booking_id: int, db: Session = Depends(get_db)):
    """
    Get all active bids for a lesson (top 10 ranked bids)
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Get top 10 ranked bids
    bids = db.query(LessonBid).filter(
        LessonBid.booking_id == booking_id,
        LessonBid.bid_status == BidStatus.ACTIVE.value,
        LessonBid.bid_rank.isnot(None)
    ).order_by(LessonBid.bid_rank.asc()).all()
    
    results = []
    for bid in bids:
        tutor = db.query(Tutor).filter(Tutor.id == bid.tutor_id).first()
        user = db.query(User).filter(User.id == tutor.user_id).first() if tutor else None
        
        results.append({
            "bid_id": bid.id,
            "bid_rank": bid.bid_rank,
            "tutor_id": tutor.id if tutor else None,
            "tutor_name": user.username if user else "Instructor",
            "tutor_rating": tutor.rating if tutor else 4.0,
            "tutor_experience": tutor.years_experience if tutor else 0,
            "total_lessons": tutor.total_lessons if tutor else 0,
            "bid_amount_per_hour": bid.bid_amount_per_hour,
            "total_bid_amount": bid.total_bid_amount,
            "tutor_message": bid.tutor_message,
            "created_at": bid.created_at.isoformat()
        })
    
    return {
        "booking_id": booking_id,
        "lesson_type": booking.lesson_type,
        "lesson_date": booking.lesson_date.isoformat(),
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "duration_hours": booking.duration_hours,
        "pickup_location": booking.pickup_location,
        "status": booking.status,
        "bidding_closes_at": booking.bidding_closes_at.isoformat() if booking.bidding_closes_at else None,
        "total_bids": booking.total_bids,
        "bids": results
    }


@router.post("/select-tutor")
async def select_tutor(request: SelectTutorRequest, db: Session = Depends(get_db)):
    """
    Student selects a tutor from the bids
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != LessonStatus.BIDDING_OPEN.value:
        raise HTTPException(status_code=400, detail="Tutor has already been selected or bidding is closed")
    
    # Get selected bid
    selected_bid = db.query(LessonBid).filter(LessonBid.id == request.selected_bid_id).first()
    if not selected_bid or selected_bid.booking_id != request.booking_id:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get tutor info for notification
    selected_tutor = db.query(Tutor).filter(Tutor.id == selected_bid.tutor_id).first()
    student = db.query(User).filter(User.id == booking.student_id).first()
    
    # Update booking
    booking.tutor_id = selected_bid.tutor_id
    booking.final_price = selected_bid.total_bid_amount
    booking.platform_fee = calculate_platform_fee(selected_bid.total_bid_amount)
    booking.tutor_payout = selected_bid.total_bid_amount - booking.platform_fee
    booking.status = LessonStatus.TUTOR_SELECTED.value
    
    # Update bids
    selected_bid.bid_status = BidStatus.SELECTED.value
    selected_bid.selected_at = datetime.utcnow()
    
    # Reject all other bids
    other_bids = db.query(LessonBid).filter(
        LessonBid.booking_id == request.booking_id,
        LessonBid.id != request.selected_bid_id,
        LessonBid.bid_status == BidStatus.ACTIVE.value
    ).all()
    for bid in other_bids:
        bid.bid_status = BidStatus.REJECTED.value
    
    db.commit()
    
    # Send notification to selected tutor
    if websocket_manager and selected_tutor:
        await websocket_manager.send_to_user(selected_tutor.user_id, {
            "type": "tutor_selected",
            "booking_id": booking.id,
            "student_name": student.username if student else "Student",
            "lesson_date": booking.lesson_date.isoformat(),
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_hours": booking.duration_hours,
            "lesson_type": booking.lesson_type,
            "pickup_location": booking.pickup_location,
            "final_price": booking.final_price,
            "tutor_payout": booking.tutor_payout,
            "message": "🎉 Congratulations! A student selected you for a lesson. Please accept or decline."
        })
    
    # Send rejection notification to other tutors
    if websocket_manager:
        for bid in other_bids:
            rejected_tutor = db.query(Tutor).filter(Tutor.id == bid.tutor_id).first()
            if rejected_tutor:
                await websocket_manager.send_to_user(rejected_tutor.user_id, {
                    "type": "bid_rejected",
                    "booking_id": booking.id,
                    "message": "Your bid was not selected for this lesson."
                })
    
    return {
        "message": "Tutor selected successfully! Awaiting tutor confirmation.",
        "tutor_id": selected_bid.tutor_id,
        "final_price": booking.final_price,
        "platform_fee": booking.platform_fee,
        "tutor_payout": booking.tutor_payout,
        "status": booking.status
    }


@router.post("/tutor-respond")
async def tutor_respond_to_selection(request: TutorAcceptRequest, db: Session = Depends(get_db)):
    """
    Tutor accepts or rejects a lesson after being selected by student
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != LessonStatus.TUTOR_SELECTED.value:
        raise HTTPException(status_code=400, detail="This lesson is not pending tutor confirmation")
    
    if booking.tutor_id != request.tutor_id:
        raise HTTPException(status_code=403, detail="You are not the selected tutor for this lesson")
    
    tutor = db.query(Tutor).filter(Tutor.id == request.tutor_id).first()
    student = db.query(User).filter(User.id == booking.student_id).first()
    tutor_user = db.query(User).filter(User.id == tutor.user_id).first() if tutor else None
    
    if request.accept:
        # Tutor accepts the lesson
        booking.status = LessonStatus.CONFIRMED.value
        booking.confirmed_at = datetime.utcnow()
        
        # Create progress tracker
        progress = LessonProgress(booking_id=booking.id)
        db.add(progress)
        
        db.commit()
        
        # Notify student
        if websocket_manager and student:
            await websocket_manager.send_to_user(student.id, {
                "type": "lesson_confirmed",
                "booking_id": booking.id,
                "tutor_name": tutor_user.username if tutor_user else "Tutor",
                "lesson_date": booking.lesson_date.isoformat(),
                "start_time": booking.start_time,
                "final_price": booking.final_price,
                "message": f"🎉 Great news! {tutor_user.username if tutor_user else 'Your tutor'} has confirmed your lesson!"
            })
        
        return {
            "message": "Lesson confirmed! Get ready to teach!",
            "booking_id": booking.id,
            "status": booking.status,
            "student_name": student.username if student else "Student",
            "lesson_date": booking.lesson_date.isoformat(),
            "start_time": booking.start_time,
            "final_price": booking.final_price
        }
    else:
        # Tutor rejects the lesson
        booking.status = LessonStatus.CANCELLED.value
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = request.reject_reason or "Tutor declined after being selected"
        booking.tutor_id = None
        
        # Mark the bid as rejected
        selected_bid = db.query(LessonBid).filter(
            LessonBid.booking_id == booking.id,
            LessonBid.tutor_id == request.tutor_id
        ).first()
        if selected_bid:
            selected_bid.bid_status = BidStatus.REJECTED.value
        
        db.commit()
        
        # Notify student
        if websocket_manager and student:
            await websocket_manager.send_to_user(student.id, {
                "type": "lesson_cancelled",
                "booking_id": booking.id,
                "reason": "The selected tutor is unavailable. Please create a new booking.",
                "message": "😔 Unfortunately, the tutor declined. Please book another lesson."
            })
        
        return {
            "message": "Lesson declined. Student has been notified.",
            "booking_id": booking.id,
            "status": booking.status
        }


@router.get("/pending-acceptance/{tutor_id}")
async def get_pending_acceptances(tutor_id: int, db: Session = Depends(get_db)):
    """
    Get all lessons pending tutor acceptance
    """
    bookings = db.query(LessonBooking).filter(
        LessonBooking.tutor_id == tutor_id,
        LessonBooking.status == LessonStatus.TUTOR_SELECTED.value
    ).order_by(LessonBooking.created_at.desc()).all()
    
    results = []
    for booking in bookings:
        student = db.query(User).filter(User.id == booking.student_id).first()
        bid = db.query(LessonBid).filter(
            LessonBid.booking_id == booking.id,
            LessonBid.tutor_id == tutor_id
        ).first()
        
        results.append({
            "booking_id": booking.id,
            "student_name": student.username if student else "Student",
            "lesson_date": booking.lesson_date.isoformat(),
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_hours": booking.duration_hours,
            "lesson_type": booking.lesson_type,
            "pickup_location": booking.pickup_location,
            "pickup_lat": booking.pickup_lat,
            "pickup_lng": booking.pickup_lng,
            "student_vehicle": booking.student_vehicle,
            "special_requirements": booking.special_requirements,
            "final_price": booking.final_price,
            "tutor_payout": booking.tutor_payout,
            "your_bid_message": bid.tutor_message if bid else None,
            "selected_at": bid.selected_at.isoformat() if bid and bid.selected_at else None,
            "created_at": booking.created_at.isoformat()
        })
    
    return {
        "pending_lessons": results,
        "count": len(results)
    }


@router.get("/booking/{booking_id}")
async def get_booking_details(booking_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific booking
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    student = db.query(User).filter(User.id == booking.student_id).first()
    
    tutor_info = None
    if booking.tutor_id:
        tutor = db.query(Tutor).filter(Tutor.id == booking.tutor_id).first()
        tutor_user = db.query(User).filter(User.id == tutor.user_id).first() if tutor else None
        if tutor and tutor_user:
            tutor_info = {
                "tutor_id": tutor.id,
                "name": tutor_user.username,
                "rating": tutor.rating,
                "experience": tutor.years_experience,
                "total_lessons": tutor.total_lessons
            }
    
    return {
        "booking_id": booking.id,
        "student_id": booking.student_id,
        "student_name": student.username if student else "Student",
        "lesson_date": booking.lesson_date.isoformat(),
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "duration_hours": booking.duration_hours,
        "lesson_type": booking.lesson_type,
        "pickup_location": booking.pickup_location,
        "pickup_lat": booking.pickup_lat,
        "pickup_lng": booking.pickup_lng,
        "student_vehicle": booking.student_vehicle,
        "special_requirements": booking.special_requirements,
        "status": booking.status,
        "tutor": tutor_info,
        "final_price": booking.final_price,
        "platform_fee": booking.platform_fee,
        "tutor_payout": booking.tutor_payout,
        "payment_status": booking.payment_status,
        "total_bids": booking.total_bids,
        "created_at": booking.created_at.isoformat(),
        "confirmed_at": booking.confirmed_at.isoformat() if booking.confirmed_at else None,
        "started_at": booking.started_at.isoformat() if booking.started_at else None,
        "completed_at": booking.completed_at.isoformat() if booking.completed_at else None
    }


@router.post("/confirm/{booking_id}")
async def confirm_lesson(booking_id: int, db: Session = Depends(get_db)):
    """
    Confirm lesson after payment
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != LessonStatus.TUTOR_SELECTED.value:
        raise HTTPException(status_code=400, detail="Cannot confirm lesson in current status")
    
    booking.status = LessonStatus.CONFIRMED.value
    booking.confirmed_at = datetime.utcnow()
    booking.payment_status = "completed"
    
    # Create progress tracker
    progress = LessonProgress(booking_id=booking_id)
    db.add(progress)
    
    db.commit()
    
    return {"message": "Lesson confirmed successfully!"}


@router.post("/start/{booking_id}")
async def start_lesson(booking_id: int, tutor_id: int, db: Session = Depends(get_db)):
    """
    Start a confirmed lesson (called by tutor)
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.tutor_id != tutor_id:
        raise HTTPException(status_code=403, detail="You are not the assigned tutor")
    
    if booking.status != LessonStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="Lesson must be confirmed before starting")
    
    booking.status = LessonStatus.IN_PROGRESS.value
    booking.started_at = datetime.utcnow()
    db.commit()
    
    # Notify student
    student = db.query(User).filter(User.id == booking.student_id).first()
    if websocket_manager and student:
        await websocket_manager.send_to_user(student.id, {
            "type": "lesson_started",
            "booking_id": booking.id,
            "message": "🚗 Your driving lesson has started!"
        })
    
    return {
        "message": "Lesson started!",
        "booking_id": booking.id,
        "started_at": booking.started_at.isoformat()
    }


@router.post("/complete/{booking_id}")
async def complete_lesson(booking_id: int, tutor_id: int, db: Session = Depends(get_db)):
    """
    Complete a lesson in progress (called by tutor)
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.tutor_id != tutor_id:
        raise HTTPException(status_code=403, detail="You are not the assigned tutor")
    
    if booking.status != LessonStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=400, detail="Lesson must be in progress to complete")
    
    booking.status = LessonStatus.COMPLETED.value
    booking.completed_at = datetime.utcnow()
    
    # Update tutor stats
    tutor = db.query(Tutor).filter(Tutor.id == booking.tutor_id).first()
    if tutor:
        tutor.total_lessons += 1
        tutor.total_earnings += booking.tutor_payout
    
    db.commit()
    
    # Notify student
    student = db.query(User).filter(User.id == booking.student_id).first()
    if websocket_manager and student:
        await websocket_manager.send_to_user(student.id, {
            "type": "lesson_completed",
            "booking_id": booking.id,
            "final_price": booking.final_price,
            "message": "🎉 Your lesson is complete! Please rate your instructor."
        })
    
    return {
        "message": "Lesson completed successfully!",
        "booking_id": booking.id,
        "completed_at": booking.completed_at.isoformat(),
        "tutor_payout": booking.tutor_payout
    }


@router.post("/rate-student")
async def rate_student(booking_id: int, request: RatingRequest, db: Session = Depends(get_db)):
    """
    Tutor rates the student after lesson
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != LessonStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Can only rate completed lessons")
    
    booking.tutor_rating = request.rating
    booking.tutor_feedback = request.feedback
    db.commit()
    
    return {"message": "Student rated successfully!"}


@router.post("/rate-tutor")
async def rate_tutor(request: RatingRequest, db: Session = Depends(get_db)):
    """
    Student rates the tutor after lesson
    """
    booking = db.query(LessonBooking).filter(LessonBooking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != LessonStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Can only rate completed lessons")
    
    booking.student_rating = request.rating
    booking.student_feedback = request.feedback
    
    # Update tutor's overall rating (weighted average)
    tutor = db.query(Tutor).filter(Tutor.id == booking.tutor_id).first()
    if tutor:
        total_lessons = tutor.total_lessons
        current_rating = tutor.rating
        new_rating = ((current_rating * (total_lessons - 1)) + request.rating) / total_lessons
        tutor.rating = round(new_rating, 2)
    
    db.commit()
    
    return {"message": "Tutor rated successfully!", "new_rating": tutor.rating if tutor else None}


@router.get("/student/{student_id}")
async def get_student_lessons(student_id: int, db: Session = Depends(get_db)):
    """
    Get all lessons for a student
    """
    bookings = db.query(LessonBooking).filter(
        LessonBooking.student_id == student_id
    ).order_by(LessonBooking.created_at.desc()).all()
    
    results = []
    for booking in bookings:
        tutor_info = None
        if booking.tutor_id:
            tutor = db.query(Tutor).filter(Tutor.id == booking.tutor_id).first()
            if tutor:
                user = db.query(User).filter(User.id == tutor.user_id).first()
                tutor_info = {
                    "tutor_id": tutor.id,
                    "name": user.username if user else "Instructor",
                    "rating": tutor.rating
                }
        
        results.append({
            "booking_id": booking.id,
            "lesson_date": booking.lesson_date.isoformat(),
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_hours": booking.duration_hours,
            "lesson_type": booking.lesson_type,
            "pickup_location": booking.pickup_location,
            "status": booking.status,
            "tutor": tutor_info,
            "final_price": booking.final_price,
            "total_bids": booking.total_bids,
            "bidding_closes_at": booking.bidding_closes_at.isoformat() if booking.bidding_closes_at else None,
            "created_at": booking.created_at.isoformat()
        })
    
    return {"bookings": results, "count": len(results)}


@router.get("/tutor/{tutor_id}")
async def get_tutor_lessons(tutor_id: int, db: Session = Depends(get_db)):
    """
    Get all lessons for a tutor
    """
    bookings = db.query(LessonBooking).filter(
        LessonBooking.tutor_id == tutor_id
    ).order_by(LessonBooking.lesson_date.desc()).all()
    
    results = []
    for booking in bookings:
        student = db.query(User).filter(User.id == booking.student_id).first()
        
        results.append({
            "booking_id": booking.id,
            "student_name": student.username,
            "lesson_date": booking.lesson_date.isoformat(),
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_hours": booking.duration_hours,
            "lesson_type": booking.lesson_type,
            "status": booking.status,
            "final_price": booking.final_price,
            "tutor_payout": booking.tutor_payout,
            "student_rating": booking.student_rating,
            "created_at": booking.created_at.isoformat()
        })
    
    return {"lessons": results, "count": len(results)}
