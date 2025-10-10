"""
Database Migration Script
Adds new columns to Ride table for offer system

Run this BEFORE starting the server with new code
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from server.app.db.database import engine, SessionLocal


def migrate_database():
    """Add new columns to rides table"""
    
    print("🔄 Starting database migration...")
    
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='rides' AND column_name='offered_to_driver_id'
        """))
        
        if result.fetchone():
            print("✅ Columns already exist - migration not needed")
            return
        
        # Add new columns
        print("📝 Adding new columns to rides table...")
        
        db.execute(text("""
            ALTER TABLE rides 
            ADD COLUMN IF NOT EXISTS offered_to_driver_id INTEGER,
            ADD COLUMN IF NOT EXISTS offered_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS offer_attempts INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS declined_driver_ids TEXT,
            ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP;
        """))
        
        # Add indexes for performance
        print("📝 Adding indexes...")
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rides_created_at ON rides(created_at);
        """))
        
        db.commit()
        
        print("✅ Migration completed successfully!")
        print("\nNew columns added:")
        print("  - offered_to_driver_id: Tracks current driver being offered")
        print("  - offered_at: When offer was made")
        print("  - expires_at: When offer expires")
        print("  - offer_attempts: Number of drivers tried")
        print("  - declined_driver_ids: Comma-separated list of decliners")
        print("  - cancelled_at: When ride was cancelled")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_database()
