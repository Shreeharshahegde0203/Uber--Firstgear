"""
Database Migration Script
Adds service area columns to Tutor table for location-based notifications

Run this BEFORE starting the server with updated tutor code
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from server.app.db.database import engine, SessionLocal


def migrate_tutor_service_area():
    """Add service area columns to tutors table"""
    
    print("🔄 Starting tutor service area migration...")
    
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='tutors' AND column_name='service_area_lat'
        """))
        
        if result.fetchone():
            print("✅ Service area columns already exist - migration not needed")
            return
        
        # Add new columns
        print("📝 Adding service area columns to tutors table...")
        
        db.execute(text("""
            ALTER TABLE tutors 
            ADD COLUMN IF NOT EXISTS service_area_lat FLOAT,
            ADD COLUMN IF NOT EXISTS service_area_lng FLOAT,
            ADD COLUMN IF NOT EXISTS service_radius_km FLOAT DEFAULT 20.0;
        """))
        
        db.commit()
        
        print("✅ Migration completed successfully!")
        print("📍 Tutors can now specify their service area for location-based notifications")
        print("   - service_area_lat: Center latitude of service area")
        print("   - service_area_lng: Center longitude of service area")
        print("   - service_radius_km: Max distance willing to travel (default: 20km)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        migrate_tutor_service_area()
    except Exception as e:
        print(f"\n💥 Error during migration: {str(e)}")
        sys.exit(1)
