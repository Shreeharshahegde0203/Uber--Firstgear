from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from ..db.database import get_db
from ..db.models import Ride, User
from ..core.request_models import RideRequest
from ..core.schemas import RideResponse

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/request", response_model=RideResponse)
def request_ride(ride_request: RideRequest, db: Session = Depends(get_db)):
    """
    Endpoint to handle ride requests.
    Now triggers automatic driver matching via background worker.
    
    Edge cases handled:
    - User not found
    - Invalid coordinates
    - Duplicate requests (rapid clicking)
    - Database failures
    - Rider has pending ride
    
    Parameters:
    - source_location: Starting point
    - dest_location: Destination 
    - user_id: ID of the requesting user
    
    Returns:
    - Ride details including ID and status
    """
    try:
        # 1. Validate user exists and is not a driver
        user = db.query(User).filter(User.id == ride_request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {ride_request.user_id} not found"
            )
        
        if user.is_driver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Drivers cannot request rides"
            )
        
        # 2. Check for existing pending rides (prevent duplicate requests)
        existing_ride = db.query(Ride).filter(
            Ride.rider_id == ride_request.user_id,
            Ride.status.in_(["requested", "offering", "accepted"])
        ).first()
        
        if existing_ride:
            logger.warning(f"User #{ride_request.user_id} already has pending ride #{existing_ride.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have a pending ride (ID: {existing_ride.id})"
            )
        
        # 3. Validate coordinates
        if ride_request.pickup_lat is None or ride_request.pickup_lng is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pickup coordinates are required"
            )
        
        if not (-90 <= ride_request.pickup_lat <= 90):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pickup latitude (must be between -90 and 90)"
            )
        
        if not (-180 <= ride_request.pickup_lng <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pickup longitude (must be between -180 and 180)"
            )
        
        # 4. Update rider's current location
        user.latitude = ride_request.pickup_lat
        user.longitude = ride_request.pickup_lng
        
        # 5. Create new ride record
        new_ride = Ride(
            rider_id=ride_request.user_id,
            start_location=ride_request.source_location,
            end_location=ride_request.dest_location,
            start_lat=ride_request.pickup_lat,
            start_lng=ride_request.pickup_lng,
            end_lat=ride_request.dest_lat,
            end_lng=ride_request.dest_lng,
            status="requested"  # Background worker will pick this up
        )
        
        # 6. Store in database
        db.add(new_ride)
        db.commit()
        db.refresh(new_ride)
        
        logger.info(f"✅ Ride #{new_ride.id} created: {ride_request.source_location} → {ride_request.dest_location} (rider #{ride_request.user_id})")
        
        return new_ride
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        # Log unexpected errors
        logger.error(f"❌ Unexpected error creating ride: {e}", exc_info=True)
        db.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )
