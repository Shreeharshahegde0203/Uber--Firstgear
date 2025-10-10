"""
Set All Drivers Online - Use if drivers are stuck offline
"""
import sys
sys.path.insert(0, '../server')

from app.db.database import SessionLocal
from app.db.models import User

def main():
    print("\n🚨 Setting all drivers ONLINE")
    print("="*60)
    
    db = SessionLocal()
    try:
        drivers = db.query(User).filter(User.is_driver == True).all()
        
        for driver in drivers:
            driver.availability = True
        
        db.commit()
        
        print(f"\n✅ Set {len(drivers)} drivers online")
        for d in drivers:
            print(f"   🟢 Driver #{d.id}: {d.username}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
