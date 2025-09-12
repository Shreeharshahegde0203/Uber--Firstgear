from pydantic import BaseModel
from typing import Optional, Union

class RideRequest(BaseModel):
    source_location: str
    dest_location: str
    user_id: int
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None
