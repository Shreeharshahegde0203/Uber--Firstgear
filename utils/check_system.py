"""
System Check Utility - Check all system components
Run this if anything isn't working
"""
import sys
sys.path.insert(0, '../server')

from app.db.database import SessionLocal
from app.db.models import User, Ride

def main():
    print("\n🔍 SYSTEM STATUS CHECK")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Check drivers
        drivers = db.query(User).filter(User.is_driver == True).all()
        online_drivers = [d for d in drivers if d.availability]
        
        print(f"\n📊 DRIVERS: {len(drivers)} total, {len(online_drivers)} online")
        for d in drivers:
            status = "🟢 ONLINE" if d.availability else "🔴 OFFLINE"
            print(f"   {status} Driver #{d.id}: {d.username}")
        
        # Check riders
        riders = db.query(User).filter(User.is_driver == False).all()
        print(f"\n📊 RIDERS: {len(riders)} total")
        
        # Check rides
        rides = db.query(Ride).all()
        pending_rides = [r for r in rides if r.status == "requested"]
        
        print(f"\n📊 RIDES: {len(rides)} total, {len(pending_rides)} pending")
        if pending_rides:
            for r in pending_rides:
                print(f"   Ride #{r.id}: Waiting for driver")
        
        # Warnings
        if len(online_drivers) == 0:
            print(f"\n⚠️  WARNING: No drivers online!")
            print(f"   Run: python utils/set_drivers_online.py")
        
        print(f"\n✅ System check complete")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
