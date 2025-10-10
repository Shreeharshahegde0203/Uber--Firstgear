"""
Advanced Matching Engine for Ride-Hailing System
Handles automatic driver matching with offer/accept/decline flow
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..db.models import User, Ride
from ..db.database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    Core matching engine that handles ride-driver matching with offer system
    """
    
    OFFER_TIMEOUT_SECONDS = 20  # Changed from 15 to 20 seconds
    MAX_OFFER_ATTEMPTS = 5  # Maximum number of drivers to try per ride
    MATCHING_INTERVAL_SECONDS = 1  # How often to check for new rides
    SEARCH_RADIUS_KM = 10  # Initial search radius
    RADIUS_INCREMENT_KM = 5  # Increase radius after failed attempts
    
    def __init__(self):
        self.running = False
        self.websocket_manager = None  # Will be set from main.py
        
    def set_websocket_manager(self, manager):
        """Set the WebSocket manager for push notifications"""
        self.websocket_manager = manager
        
    async def start(self):
        """Start the background matching worker"""
        self.running = True
        logger.info("🚀 Matching Engine started")
        
        # Start multiple concurrent workers
        await asyncio.gather(
            self._matching_worker(),
            self._expiry_worker(),
            self._cleanup_worker()
        )
    
    async def stop(self):
        """Stop the matching engine"""
        self.running = False
        logger.info("🛑 Matching Engine stopped")
    
    # ============================================
    # MAIN MATCHING WORKER
    # ============================================
    
    async def _matching_worker(self):
        """
        Continuously process requested rides in FIFO order
        Handles the entire offer lifecycle
        """
        logger.info("🔄 Matching worker started")
        
        while self.running:
            db = SessionLocal()
            try:
                # Process one ride at a time (FIFO)
                await self._process_next_ride(db)
                
            except Exception as e:
                logger.error(f"❌ Error in matching worker: {e}", exc_info=True)
            finally:
                db.close()
            
            # Wait before next iteration
            await asyncio.sleep(self.MATCHING_INTERVAL_SECONDS)
    
    async def _process_next_ride(self, db: Session):
        """
        Process the oldest requested ride WITHOUT active offer (FIFO)
        
        Edge cases handled:
        - No rides available
        - No drivers available
        - Driver went offline
        - All drivers declined
        - Rider cancelled during offering
        - One offer per driver at a time (queue system)
        """
        # Get oldest requested ride WITHOUT current active offer (FIFO + Queue)
        ride = db.query(Ride).filter(
            Ride.status == "requested",
            Ride.current_offer_driver_id == None  # NEW: No active offer
        ).order_by(Ride.created_at.asc()).with_for_update(skip_locked=True).first()
        
        if not ride:
            return  # No rides to process
        
        logger.info(f"🎯 Processing ride #{ride.id} for rider #{ride.rider_id}")
        
        # Check if ride was cancelled while we were fetching it
        if ride.status == "cancelled":
            logger.info(f"⚠️ Ride #{ride.id} was cancelled, skipping")
            return
        
        # Get excluded driver IDs (those who already declined)
        excluded_driver_ids = self._get_excluded_drivers(ride)
        
        # Find nearest available driver
        driver = self._find_nearest_driver(
            db,
            ride.start_lat,
            ride.start_lng,
            excluded_driver_ids,
            search_radius_km=self.SEARCH_RADIUS_KM + (ride.offer_attempts * self.RADIUS_INCREMENT_KM)
        )
        
        if not driver:
            logger.warning(f"⚠️ No available drivers found for ride #{ride.id} (attempt {ride.offer_attempts + 1}) - will keep retrying...")
            return
        
        # Create offer
        await self._create_offer(db, ride, driver)
    
    def _find_nearest_driver(
        self,
        db: Session,
        pickup_lat: float,
        pickup_lng: float,
        excluded_driver_ids: List[int],
        search_radius_km: float
    ) -> Optional[User]:
        """
        Find the nearest available driver using Haversine formula
        
        Edge cases handled:
        - No drivers in database
        - All drivers offline
        - All drivers excluded (declined)
        - Drivers with no location data
        - Invalid coordinates
        - Drivers with pending offers (one-offer-per-driver rule)
        """
        if pickup_lat is None or pickup_lng is None:
            logger.error("❌ Invalid pickup coordinates")
            return None
        
        # NEW: Get drivers who currently have pending offers (to exclude them)
        now = datetime.utcnow()
        drivers_with_offers = db.query(Ride.current_offer_driver_id).filter(
            and_(
                Ride.current_offer_driver_id.isnot(None),
                Ride.offer_expires_at > now,
                Ride.status == "requested"
            )
        ).all()
        busy_driver_ids = [d[0] for d in drivers_with_offers if d[0]]
        
        # Get available drivers (not currently on a ride, no pending offers)
        query = db.query(User).filter(
            and_(
                User.is_driver == True,
                User.availability == True,
                User.latitude.isnot(None),
                User.longitude.isnot(None)
            )
        )
        
        # Exclude drivers who already declined
        if excluded_driver_ids:
            query = query.filter(~User.id.in_(excluded_driver_ids))
        
        # NEW: Exclude drivers with pending offers (one-offer-per-driver)
        if busy_driver_ids:
            query = query.filter(~User.id.in_(busy_driver_ids))
            logger.info(f"🚫 Excluding {len(busy_driver_ids)} drivers with pending offers: {busy_driver_ids}")
        
        available_drivers = query.all()
        
        if not available_drivers:
            return None
        
        # Calculate distances and find nearest
        import math
        
        def haversine(lat1, lon1, lat2, lon2):
            """Calculate distance between two points on Earth"""
            R = 6371  # Earth radius in km
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        closest_driver = None
        min_distance = float('inf')
        
        for driver in available_drivers:
            try:
                distance = haversine(
                    pickup_lat, pickup_lng,
                    driver.latitude, driver.longitude
                )
                
                # Only consider drivers within search radius
                if distance <= search_radius_km and distance < min_distance:
                    min_distance = distance
                    closest_driver = driver
                    
            except Exception as e:
                logger.error(f"❌ Error calculating distance for driver #{driver.id}: {e}")
                continue
        
        if closest_driver:
            logger.info(f"✅ Found driver #{closest_driver.id} at {min_distance:.2f}km")
        
        return closest_driver
    
    async def _create_offer(self, db: Session, ride: Ride, driver: User):
        """
        Create an offer to a driver with timeout
        
        Edge cases handled:
        - Driver went offline while processing
        - Ride was cancelled
        - Database commit failures
        """
        try:
            # Double-check driver is still available
            db.refresh(driver)
            if not driver.availability:
                logger.warning(f"⚠️ Driver #{driver.id} went offline, skipping")
                return
            
            # Update ride status to offering
            ride.status = "offering"
            ride.offered_to_driver_id = driver.id
            ride.offered_at = datetime.utcnow()
            ride.expires_at = datetime.utcnow() + timedelta(seconds=self.OFFER_TIMEOUT_SECONDS)
            ride.offer_attempts += 1
            
            # NEW: Track current offer for queue management
            ride.current_offer_driver_id = driver.id
            ride.offer_expires_at = datetime.utcnow() + timedelta(seconds=self.OFFER_TIMEOUT_SECONDS)
            
            db.commit()
            db.refresh(ride)
            
            logger.info(f"📤 Offer created: Ride #{ride.id} → Driver #{driver.id} (expires in {self.OFFER_TIMEOUT_SECONDS}s)")
            
            # Send WebSocket notification to driver
            await self._notify_driver_offer(driver.id, ride)
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to create offer: {e}", exc_info=True)
    
    def _get_excluded_drivers(self, ride: Ride) -> List[int]:
        """Parse declined driver IDs from comma-separated string"""
        if not ride.declined_driver_ids:
            return []
        
        try:
            return [int(id.strip()) for id in ride.declined_driver_ids.split(',') if id.strip()]
        except Exception as e:
            logger.error(f"❌ Error parsing declined drivers: {e}")
            return []
    
    def _count_available_drivers(self, db: Session, excluded_driver_ids: List[int]) -> int:
        """
        Count available drivers (continuously updated pool)
        Excludes offline drivers, drivers with active rides, and declined drivers
        """
        # Get drivers with pending offers (to exclude)
        now = datetime.utcnow()
        drivers_with_offers = db.query(Ride.current_offer_driver_id).filter(
            and_(
                Ride.current_offer_driver_id.isnot(None),
                Ride.offer_expires_at > now,
                Ride.status.in_(["requested", "offering"])
            )
        ).all()
        busy_driver_ids = [d[0] for d in drivers_with_offers if d[0]]
        
        # Count available drivers
        query = db.query(User).filter(
            and_(
                User.is_driver == True,
                User.availability == True
            )
        )
        
        # Exclude declined drivers
        if excluded_driver_ids:
            query = query.filter(~User.id.in_(excluded_driver_ids))
        
        # Exclude drivers with pending offers
        if busy_driver_ids:
            query = query.filter(~User.id.in_(busy_driver_ids))
        
        count = query.count()
        logger.info(f"📊 Available drivers: {count} (excluded: {len(excluded_driver_ids)} declined, {len(busy_driver_ids)} with pending offers)")
        return count
    
    # ============================================
    # EXPIRY WORKER
    # ============================================
    
    async def _expiry_worker(self):
        """
        Continuously check for expired offers and revert them to 'requested'
        Runs every 2 seconds
        """
        logger.info("⏰ Expiry worker started")
        
        while self.running:
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                
                # Find expired offers
                expired_rides = db.query(Ride).filter(
                    and_(
                        Ride.status == "offering",
                        Ride.expires_at <= now
                    )
                ).all()
                
                for ride in expired_rides:
                    expired_driver_id = ride.offered_to_driver_id
                    logger.warning(f"⏳ Offer expired for ride #{ride.id} (driver #{expired_driver_id}) - TIMEOUT = AUTO-DECLINE")
                    
                    # NEW BEHAVIOR: Timeout is treated as decline (move to next driver)
                    # Add driver to declined list
                    if ride.declined_driver_ids:
                        ride.declined_driver_ids += f",{expired_driver_id}"
                    else:
                        ride.declined_driver_ids = str(expired_driver_id)
                    
                    # Revert to requested for next driver
                    ride.status = "requested"
                    ride.offered_to_driver_id = None
                    ride.offered_at = None
                    ride.expires_at = None
                    
                    # NEW: Clear current offer tracking
                    ride.current_offer_driver_id = None
                    ride.offer_expires_at = None
                    
                    # NEW: Check if all drivers exhausted (continuously updated pool)
                    excluded_drivers = self._get_excluded_drivers(ride)
                    remaining_drivers = self._count_available_drivers(db, excluded_drivers)
                    
                    if remaining_drivers == 0:
                        logger.error(f"❌ All drivers exhausted for ride #{ride.id} - CANCELLING")
                        ride.status = "cancelled"
                        ride.cancelled_at = datetime.utcnow()
                        ride.cancellation_reason = "no_drivers_available"
                        db.commit()
                        
                        # Notify rider about cancellation
                        await self._notify_rider_cancelled(ride.rider_id, ride.id)
                    else:
                        logger.info(f"🔄 {remaining_drivers} drivers still available for ride #{ride.id}")
                        db.commit()
                    
                    # Notify driver that offer expired
                    await self._notify_driver_offer_expired(expired_driver_id, ride.id)
                    
            except Exception as e:
                logger.error(f"❌ Error in expiry worker: {e}", exc_info=True)
                db.rollback()
            finally:
                db.close()
            
            await asyncio.sleep(2)
    
    # ============================================
    # CLEANUP WORKER
    # ============================================
    
    async def _cleanup_worker(self):
        """
        Clean up stale rides that have been in 'requested' for too long
        Runs every 60 seconds
        """
        logger.info("🧹 Cleanup worker started")
        
        while self.running:
            db = SessionLocal()
            try:
                # Cancel rides that have been requested for more than 10 minutes
                stale_threshold = datetime.utcnow() - timedelta(minutes=10)
                
                stale_rides = db.query(Ride).filter(
                    and_(
                        Ride.status == "requested",
                        Ride.created_at < stale_threshold
                    )
                ).all()
                
                for ride in stale_rides:
                    logger.warning(f"🗑️ Cancelling stale ride #{ride.id} (created {ride.created_at})")
                    ride.status = "cancelled"
                    ride.cancelled_at = datetime.utcnow()
                    db.commit()
                    
                    # Notify rider
                    await self._notify_rider_timeout(ride.rider_id, ride.id)
                    
            except Exception as e:
                logger.error(f"❌ Error in cleanup worker: {e}", exc_info=True)
                db.rollback()
            finally:
                db.close()
            
            await asyncio.sleep(60)
    
    # ============================================
    # ACCEPT/DECLINE HANDLERS
    # ============================================
    
    async def handle_driver_accept(self, db: Session, ride_id: int, driver_id: int) -> Tuple[bool, str]:
        """
        Handle driver accepting a ride offer
        
        Edge cases handled:
        - Offer already expired
        - Ride was cancelled
        - Wrong driver accepting
        - Concurrent acceptance attempts
        
        Returns: (success: bool, message: str)
        """
        try:
            # Lock the ride row
            ride = db.query(Ride).filter(Ride.id == ride_id).with_for_update().first()
            
            if not ride:
                return False, "Ride not found"
            
            # Validate state
            if ride.status != "offering":
                return False, f"Ride is not in offering state (current: {ride.status})"
            
            # Validate it's the correct driver
            if ride.offered_to_driver_id != driver_id:
                return False, "This ride was not offered to you"
            
            # Check if expired
            if ride.expires_at and datetime.utcnow() > ride.expires_at:
                return False, "Offer has expired"
            
            # Accept the ride
            ride.status = "accepted"
            ride.driver_id = driver_id
            ride.offered_to_driver_id = None
            ride.offered_at = None
            ride.expires_at = None
            
            # NEW: Clear current offer tracking
            ride.current_offer_driver_id = None
            ride.offer_expires_at = None
            
            # Mark driver as busy
            driver = db.query(User).filter(User.id == driver_id).first()
            if driver:
                driver.availability = False
            
            db.commit()
            
            logger.info(f"✅ Ride #{ride_id} accepted by driver #{driver_id}")
            
            # Notify rider
            await self._notify_rider_driver_assigned(ride.rider_id, ride, driver)
            
            return True, "Ride accepted successfully"
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error accepting ride: {e}", exc_info=True)
            return False, f"Server error: {str(e)}"
    
    async def handle_driver_decline(self, db: Session, ride_id: int, driver_id: int) -> Tuple[bool, str]:
        """
        Handle driver declining a ride offer
        
        Edge cases handled:
        - Offer already expired
        - Ride was cancelled
        - Wrong driver declining
        
        Returns: (success: bool, message: str)
        """
        try:
            # Lock the ride row
            ride = db.query(Ride).filter(Ride.id == ride_id).with_for_update().first()
            
            if not ride:
                return False, "Ride not found"
            
            # Validate state
            if ride.status != "offering":
                return False, f"Ride is not in offering state (current: {ride.status})"
            
            # Validate it's the correct driver
            if ride.offered_to_driver_id != driver_id:
                return False, "This ride was not offered to you"
            
            logger.info(f"❌ Ride #{ride_id} declined by driver #{driver_id}")
            
            # Add to declined list
            if ride.declined_driver_ids:
                ride.declined_driver_ids += f",{driver_id}"
            else:
                ride.declined_driver_ids = str(driver_id)
            
            # Revert to requested for next driver
            ride.status = "requested"
            ride.offered_to_driver_id = None
            ride.offered_at = None
            ride.expires_at = None
            
            # NEW: Clear current offer tracking
            ride.current_offer_driver_id = None
            ride.offer_expires_at = None
            
            # NEW: Check if all drivers exhausted (immediately after decline)
            excluded_drivers = self._get_excluded_drivers(ride)
            remaining_drivers = self._count_available_drivers(db, excluded_drivers)
            
            if remaining_drivers == 0:
                logger.error(f"❌ All drivers exhausted for ride #{ride_id} - CANCELLING")
                ride.status = "cancelled"
                ride.cancelled_at = datetime.utcnow()
                ride.cancellation_reason = "no_drivers_available"
                db.commit()
                
                # Notify rider about cancellation
                await self._notify_rider_cancelled(ride.rider_id, ride.id)
                return True, "Ride cancelled - no drivers available"
            else:
                logger.info(f"🔄 {remaining_drivers} drivers still available for ride #{ride_id}")
                db.commit()
                return True, "Ride declined, will try another driver"
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error declining ride: {e}", exc_info=True)
            return False, f"Server error: {str(e)}"
    
    # ============================================
    # WEBSOCKET NOTIFICATIONS
    # ============================================
    
    async def _notify_driver_offer(self, driver_id: int, ride: Ride):
        """Send ride offer to driver via WebSocket"""
        if not self.websocket_manager:
            logger.warning(f"⚠️ WebSocket manager not set, cannot send offer to driver #{driver_id}")
            return
        
        try:
            message = {
                "type": "ride_offer_received",  # Match frontend expectation
                "ride": {
                    "id": ride.id,
                    "rider_id": ride.rider_id,
                    "start_location": ride.start_location,
                    "start_lat": ride.start_lat,
                    "start_lng": ride.start_lng,
                    "end_location": ride.end_location,
                    "end_lat": ride.end_lat,
                    "end_lng": ride.end_lng,
                    "fare": ride.fare,
                    "expires_at": ride.expires_at.isoformat() if ride.expires_at else None
                }
            }
            logger.info(f"📡 Sending WebSocket notification to driver #{driver_id}: {message['type']}")
            await self.websocket_manager.send_to_user(driver_id, message)
        except Exception as e:
            logger.error(f"❌ Failed to send offer notification to driver #{driver_id}: {e}", exc_info=True)
    
    async def _notify_driver_offer_expired(self, driver_id: int, ride_id: int):
        """Notify driver that offer expired"""
        if not self.websocket_manager or not driver_id:
            return
        
        try:
            await self.websocket_manager.send_to_user(driver_id, {
                "type": "offer_expired",
                "ride_id": ride_id
            })
        except Exception as e:
            logger.error(f"❌ Failed to send expiry notification: {e}")
    
    async def _notify_rider_driver_assigned(self, rider_id: int, ride: Ride, driver: User):
        """Notify rider that driver was assigned"""
        if not self.websocket_manager:
            return
        
        try:
            await self.websocket_manager.send_to_user(rider_id, {
                "type": "driver_assigned",
                "ride_id": ride.id,
                "driver_id": driver.id,
                "driver_name": driver.username,
                "driver_vehicle": driver.vehicle,
                "driver_rating": driver.rating
            })
        except Exception as e:
            logger.error(f"❌ Failed to send assignment notification: {e}")
    
    async def _notify_rider_no_drivers(self, rider_id: int, ride_id: int):
        """Notify rider that no drivers are available"""
        if not self.websocket_manager:
            return
        
        try:
            await self.websocket_manager.send_to_user(rider_id, {
                "type": "no_drivers_available",
                "ride_id": ride_id,
                "message": "Sorry, no drivers are available at the moment. Your ride has been cancelled."
            })
        except Exception as e:
            logger.error(f"❌ Failed to send no drivers notification: {e}")
    
    async def _notify_rider_timeout(self, rider_id: int, ride_id: int):
        """Notify rider that request timed out"""
        if not self.websocket_manager:
            return
        
        try:
            await self.websocket_manager.send_to_user(rider_id, {
                "type": "request_timeout",
                "ride_id": ride_id,
                "message": "Your ride request has timed out. Please try again."
            })
        except Exception as e:
            logger.error(f"❌ Failed to send timeout notification: {e}")
    
    async def _notify_rider_cancelled(self, rider_id: int, ride_id: int):
        """Notify rider that ride was cancelled due to no drivers available"""
        if not self.websocket_manager:
            return
        
        try:
            await self.websocket_manager.send_to_user(rider_id, {
                "type": "ride_cancelled",
                "ride_id": ride_id,
                "reason": "no_drivers_available",
                "message": "No drivers available. Please try again."
            })
            logger.info(f"📱 Sent cancellation notification to rider #{rider_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send cancellation notification: {e}")


# Global matching engine instance
matching_engine = MatchingEngine()
