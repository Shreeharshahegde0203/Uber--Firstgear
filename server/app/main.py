from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .db.database import engine
from .db.models import Base
from .api import ping, users, rides, ride_requests

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Mini Uber API",
    description="A simplified Uber-like API built with FastAPI",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ping.router, prefix="/api", tags=["system"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(rides.router, prefix="/api/rides", tags=["rides"])
app.include_router(ride_requests.router, prefix="/api/ride", tags=["ride-requests"])
