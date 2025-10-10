"""
Clean Database - Remove all rides (use for testing)
"""
import sys
sys.path.insert(0, '../server')

from app.db.database import SessionLocal
from app.db.models import Ride

def main():
    confirm = input("⚠️  Delete ALL rides? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled")
        return
    
    db = SessionLocal()
    try:
        count = db.query(Ride).count()
        db.query(Ride).delete()
        db.commit()
        print(f"✅ Deleted {count} rides")
    finally:
        db.close()

if __name__ == "__main__":
    main()
