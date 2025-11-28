"""
Bidding Engine Service
Background worker that manages the bidding lifecycle
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List

from ..db.database import SessionLocal
from ..db.models import LessonBooking, LessonBid, LessonStatus, BidStatus, Tutor
import threading


class BiddingEngine:
    """
    Manages the entire bidding process lifecycle
    """
    
    def __init__(self):
        self.running = False
        self.check_interval = 5  # Check every 5 seconds
        
    def start(self):
        """Start the bidding engine background worker"""
        if not self.running:
            self.running = True
            # Run in separate thread
            threading.Thread(target=self._run_worker, daemon=True).start()
            print("✅ Bidding Engine started")
    
    def stop(self):
        """Stop the bidding engine"""
        self.running = False
        print("🛑 Bidding Engine stopped")
    
    def _run_worker(self):
        """Main worker loop"""
        while self.running:
            try:
                self._process_bidding_cycle()
            except Exception as e:
                print(f"❌ Bidding Engine error: {e}")
            
            # Wait before next check
            import time
            time.sleep(self.check_interval)
    
    def _process_bidding_cycle(self):
        """Process all active bidding operations"""
        db = SessionLocal()
        try:
            # 1. Close expired bidding windows
            self._close_expired_bidding(db)
            
            # 2. Auto-select top bid if student hasn't selected (optional)
            # self._auto_select_bids(db)
            
            # 3. Send reminders to tutors about closing soon
            self._send_bidding_reminders(db)
            
        finally:
            db.close()
    
    def _close_expired_bidding(self, db: Session):
        """
        Close bidding windows that have expired
        """
        now = datetime.utcnow()
        
        # Find bookings with expired bidding windows
        expired_bookings = db.query(LessonBooking).filter(
            LessonBooking.status == LessonStatus.BIDDING_OPEN.value,
            LessonBooking.bidding_closes_at <= now
        ).all()
        
        for booking in expired_bookings:
            # Check if any bids were placed
            bid_count = db.query(LessonBid).filter(
                LessonBid.booking_id == booking.id,
                LessonBid.bid_status == BidStatus.ACTIVE.value
            ).count()
            
            if bid_count == 0:
                # No bids received - mark as cancelled
                booking.status = LessonStatus.CANCELLED.value
                booking.cancelled_at = now
                booking.cancellation_reason = "No tutors bid on this lesson"
                print(f"⏰ Booking #{booking.id} cancelled - no bids received")
            else:
                # Bids received but student hasn't selected
                # Keep status as BIDDING_OPEN but mark as "awaiting selection"
                # Student can still select a tutor
                print(f"⏰ Bidding closed for Booking #{booking.id} - {bid_count} bids received, awaiting student selection")
        
        db.commit()
    
    def _send_bidding_reminders(self, db: Session):
        """
        Send reminders to tutors when bidding is closing soon (5 mins left)
        """
        now = datetime.utcnow()
        reminder_threshold = now + timedelta(minutes=5)
        
        # Find bookings closing in next 5 minutes
        closing_soon_bookings = db.query(LessonBooking).filter(
            LessonBooking.status == LessonStatus.BIDDING_OPEN.value,
            LessonBooking.bidding_closes_at <= reminder_threshold,
            LessonBooking.bidding_closes_at > now
        ).all()
        
        for booking in closing_soon_bookings:
            # TODO: Send WebSocket/email notification to nearby tutors
            # who haven't bid yet
            print(f"⏱️ Reminder: Bidding closing soon for Booking #{booking.id}")
    
    def notify_nearby_tutors(self, booking_id: int, db: Session):
        """
        Notify tutors about new lesson request
        Finds tutors within 10km radius with matching specializations
        """
        booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
        if not booking:
            return
        
        # Find tutors with matching specialization and nearby
        from sqlalchemy import func
        
        # Simple query - in production, use PostGIS for geo queries
        tutors = db.query(Tutor).filter(
            Tutor.verification_status == "verified",
            Tutor.is_active == True,
            Tutor.specializations.contains(booking.lesson_type)
        ).limit(50).all()
        
        # TODO: Send push notification/SMS to these tutors
        print(f"📢 Notified {len(tutors)} tutors about Booking #{booking_id}")
        
        return tutors
    
    def calculate_bid_rankings(self, booking_id: int, db: Session):
        """
        Calculate and update bid rankings
        Top 10 lowest bids get ranks 1-10
        """
        bids = db.query(LessonBid).filter(
            LessonBid.booking_id == booking_id,
            LessonBid.bid_status == BidStatus.ACTIVE.value
        ).order_by(LessonBid.total_bid_amount.asc()).all()
        
        # Assign ranks to top 10
        for i, bid in enumerate(bids[:10]):
            bid.bid_rank = i + 1
            
            # Get tutor info for logging
            tutor = db.query(Tutor).filter(Tutor.id == bid.tutor_id).first()
            print(f"  Rank #{bid.bid_rank}: Tutor #{tutor.id} - ₹{bid.total_bid_amount}")
        
        # Remove ranks from others
        for bid in bids[10:]:
            bid.bid_rank = None
        
        db.commit()
        print(f"📊 Updated rankings for Booking #{booking_id} - {len(bids)} total bids, top 10 ranked")
    
    def get_booking_status(self, booking_id: int, db: Session):
        """
        Get comprehensive status of a booking including bids
        """
        booking = db.query(LessonBooking).filter(LessonBooking.id == booking_id).first()
        if not booking:
            return None
        
        # Get bid statistics
        total_bids = db.query(LessonBid).filter(
            LessonBid.booking_id == booking_id
        ).count()
        
        active_bids = db.query(LessonBid).filter(
            LessonBid.booking_id == booking_id,
            LessonBid.bid_status == BidStatus.ACTIVE.value
        ).count()
        
        # Get lowest bid
        lowest_bid = db.query(LessonBid).filter(
            LessonBid.booking_id == booking_id,
            LessonBid.bid_status == BidStatus.ACTIVE.value
        ).order_by(LessonBid.total_bid_amount.asc()).first()
        
        # Calculate time remaining
        now = datetime.utcnow()
        time_remaining = (booking.bidding_closes_at - now).total_seconds() / 60  # in minutes
        
        return {
            "booking_id": booking.id,
            "status": booking.status,
            "total_bids": total_bids,
            "active_bids": active_bids,
            "lowest_bid": lowest_bid.total_bid_amount if lowest_bid else None,
            "bidding_closes_at": booking.bidding_closes_at.isoformat(),
            "time_remaining_minutes": max(0, time_remaining),
            "bidding_closed": time_remaining <= 0
        }


# Global instance
bidding_engine = BiddingEngine()


def start_bidding_engine():
    """Start the bidding engine (called from main.py)"""
    bidding_engine.start()


def stop_bidding_engine():
    """Stop the bidding engine"""
    bidding_engine.stop()
