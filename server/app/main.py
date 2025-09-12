from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict

import os

from .db.database import engine, get_db
from .db.models import Base, Ride
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
    allow_origins=["*"],  # TODO: tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ping.router, prefix="/api", tags=["system"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(rides.router, prefix="/api/rides", tags=["rides"])
app.include_router(ride_requests.router, prefix="/api/ride", tags=["ride-requests"])


# -----------------------------
# WebSocket manager for ride sessions
# -----------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}

    async def connect(self, ride_id: int, user_type: str, websocket: WebSocket):
        await websocket.accept()
        if ride_id not in self.active_connections:
            self.active_connections[ride_id] = {}
        self.active_connections[ride_id][user_type] = websocket

    def disconnect(self, ride_id: int, user_type: str):
        if ride_id in self.active_connections:
            self.active_connections[ride_id].pop(user_type, None)
            if not self.active_connections[ride_id]:
                self.active_connections.pop(ride_id)

    async def send_location(self, ride_id: int, user_type: str, data: dict):
        other_type = "driver" if user_type == "rider" else "rider"
        if ride_id in self.active_connections and other_type in self.active_connections[ride_id]:
            await self.active_connections[ride_id][other_type].send_json(data)


manager = ConnectionManager()


@app.websocket("/ws/ride/{ride_id}/{user_type}")
async def ride_location_ws(websocket: WebSocket, ride_id: int, user_type: str):
    await manager.connect(ride_id, user_type, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.send_location(ride_id, user_type, data)
    except WebSocketDisconnect:
        manager.disconnect(ride_id, user_type)


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
