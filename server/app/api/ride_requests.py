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
    
    Parameters:
    - source_location: Starting point
    - dest_location: Destination 
    - user_id: ID of the requesting user
    
    Returns:
    - Ride details including ID and status
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == ride_request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {ride_request.user_id} not found"
            )
        
        # Create new ride record
        new_ride = Ride(
            rider_id=ride_request.user_id,
            start_location=ride_request.source_location,
            end_location=ride_request.dest_location,
            status="requested"
        )
        
        # Store in PostgreSQL
        db.add(new_ride)
        db.commit()
        db.refresh(new_ride)
        
        logger.info(f"Ride request stored in database: ID={new_ride.id}, From={ride_request.source_location}, To={ride_request.dest_location}")
        
        return new_ride
        
    except Exception as e:
        # If database operations fail, log the attempt
        logger.error(f"Failed to store ride in database: {str(e)}")
        logger.info(f"We will store this data in Postgres now: From={ride_request.source_location}, To={ride_request.dest_location}, User ID={ride_request.user_id}")
        
        # Return a mock response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
