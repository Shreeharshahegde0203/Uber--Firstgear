"""
Check Rides - View all rides in the system
"""
import sys
sys.path.insert(0, '../server')

from app.db.database import SessionLocal
from app.db.models import Ride

def main():
    print("\n📋 CURRENT RIDES")
    print("="*60)
    
    db = SessionLocal()
    try:
        rides = db.query(Ride).order_by(Ride.created_at.desc()).all()
        
        if not rides:
            print("\n   No rides in system")
            return
        
        for ride in rides:
            print(f"\n   Ride #{ride.id}")
            print(f"   Status: {ride.status}")
            print(f"   Rider: #{ride.rider_id}")
            print(f"   Driver: #{ride.driver_id or 'Not assigned'}")
            print(f"   From: {ride.start_location}")
            print(f"   To: {ride.end_location}")
            print(f"   " + "-"*50)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
