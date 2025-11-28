"""
Database Migration Script
Run this to create new tables for the driving tutor booking system
"""

from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import models AFTER loading env vars
from server.app.db.models import Base
from server.app.db.database import engine

def create_tables():
    """Create all tables defined in models.py"""
    print("🚀 Starting database migration...")
    print(f"📊 Database: {os.getenv('DATABASE_URL')}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        print("\n📋 New tables added:")
        print("  • tutors")
        print("  • tutor_availabilities")
        print("  • lesson_bookings")
        print("  • lesson_bids")
        print("  • lesson_progress")
        print("\n✨ Migration complete! You can now use the tutor booking system.")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("\n🎉 Ready to start! Run: python server.py")
    else:
        print("\n⚠️ Migration failed. Check your database connection.")
