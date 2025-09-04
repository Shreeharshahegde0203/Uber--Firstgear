from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..db.database import get_db
from ..core.schemas import PingRequest, PongResponse, UserCreate, UserResponse, RideCreate, RideResponse

router = APIRouter()

@router.post("/ping", response_model=PongResponse)
def ping_endpoint(ping_request: PingRequest):
    if ping_request.data == "ping":
        return {"message": "pong"}
    return {"message": "Invalid request"}

@router.get("/health", response_model=dict)
def health_check():
    return {"status": "healthy", "timestamp": "2023-09-03T12:00:00Z"}
