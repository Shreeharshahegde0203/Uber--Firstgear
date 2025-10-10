from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict
import logging

import os

from .db.database import engine, get_db
from .db.models import Base, Ride
from .api import ping, users, rides, ride_requests, auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    allow_origins=["*"],  # TODO: tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ping.router, prefix="/api", tags=["system"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(rides.router, prefix="/api/rides", tags=["rides"])
app.include_router(ride_requests.router, prefix="/api/ride", tags=["ride-requests"])


# -----------------------------
# WebSocket manager for ride sessions and notifications
# -----------------------------
class ConnectionManager:
    def __init__(self):
        # Ride-specific connections (old system)
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        
        # User-specific connections for push notifications (new system)
        self.user_connections: Dict[int, WebSocket] = {}

    async def connect(self, ride_id: int, user_type: str, websocket: WebSocket):
        """Connect for ride location sharing (old system)"""
        await websocket.accept()
        if ride_id not in self.active_connections:
            self.active_connections[ride_id] = {}
        self.active_connections[ride_id][user_type] = websocket

    def disconnect(self, ride_id: int, user_type: str):
        """Disconnect ride location sharing"""
        if ride_id in self.active_connections:
            self.active_connections[ride_id].pop(user_type, None)
            if not self.active_connections[ride_id]:
                self.active_connections.pop(ride_id)

    async def send_location(self, ride_id: int, user_type: str, data: dict):
        """Send location update to other party in ride"""
        other_type = "driver" if user_type == "rider" else "rider"
        if ride_id in self.active_connections and other_type in self.active_connections[ride_id]:
            await self.active_connections[ride_id][other_type].send_json(data)
    
    # New methods for user-specific notifications
    async def connect_user(self, user_id: int, websocket: WebSocket):
        """Connect a user for receiving notifications"""
        await websocket.accept()
        self.user_connections[user_id] = websocket
        logger.info(f"✅ User #{user_id} connected to notification system")
    
    def disconnect_user(self, user_id: int):
        """Disconnect user from notifications"""
        self.user_connections.pop(user_id, None)
        logger.info(f"❌ User #{user_id} disconnected from notification system")
    
    async def send_to_user(self, user_id: int, data: dict):
        """Send notification to specific user"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(data)
                logger.info(f"📤 Sent notification to user #{user_id}: {data.get('type')}")
            except Exception as e:
                logger.error(f"❌ Failed to send to user #{user_id}: {e}")
                self.disconnect_user(user_id)


manager = ConnectionManager()


# -----------------------------
# Startup and shutdown events
# -----------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize background services"""
    from .services.matching_engine import matching_engine
    
    # Connect matching engine to WebSocket manager
    matching_engine.set_websocket_manager(manager)
    
    # Start matching engine in background
    import asyncio
    asyncio.create_task(matching_engine.start())
    
    logger.info("🚀 Application started - Matching engine running")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    from .services.matching_engine import matching_engine
    await matching_engine.stop()
    logger.info("🛑 Application stopped")


# -----------------------------
# WebSocket endpoints
# -----------------------------
@app.websocket("/ws/ride/{ride_id}/{user_type}")
async def ride_location_ws(websocket: WebSocket, ride_id: int, user_type: str):
    """WebSocket for real-time location sharing during ride"""
    await manager.connect(ride_id, user_type, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.send_location(ride_id, user_type, data)
    except WebSocketDisconnect:
        manager.disconnect(ride_id, user_type)


@app.websocket("/ws/notifications/{user_id}")
async def user_notifications_ws(websocket: WebSocket, user_id: int):
    """WebSocket for push notifications (ride offers, assignments, etc.)"""
    await manager.connect_user(user_id, websocket)
    try:
        while True:
            # Keep connection alive, client can also send heartbeats
            data = await websocket.receive_json()
            
            # Handle any client messages if needed
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
                
    except WebSocketDisconnect:
        manager.disconnect_user(user_id)


# -----------------------------
# DB test endpoint
# -----------------------------
@app.get("/api/db_test")
def db_test(db: Session = Depends(get_db)):
    try:
        count = db.query(Ride).count()
        return {"success": True, "ride_count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}
