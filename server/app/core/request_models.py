from pydantic import BaseModel
from typing import Optional

class RideRequest(BaseModel):
    source_location: str
    dest_location: str
    user_id: int
