import sys
import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add server directory to path so we can import our models
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

# Load environment variables from .env file
load_dotenv()

# Get database connection string from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_sample_data():
    """Create sample data in the database"""
    from server.app.db.models import Base, User, Ride, Payment
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if we already have users (to avoid duplicates)
        existing_users = db.query(User).count()
        
        if existing_users == 0:
            print("Creating sample users...")
            
            # Create rider users
            riders = []
            for i in range(1, 4):
                hashed_password = bcrypt.hashpw(f"password{i}".encode('utf-8'), bcrypt.gensalt())
                rider = User(
                    username=f"rider{i}",
                    email=f"rider{i}@example.com",
                    hashed_password=hashed_password.decode('utf-8'),
                    is_driver=False
                )
                riders.append(rider)
                db.add(rider)
            
            # Create driver users
            drivers = []
            for i in range(1, 3):
                hashed_password = bcrypt.hashpw(f"driverpass{i}".encode('utf-8'), bcrypt.gensalt())
                driver = User(
                    username=f"driver{i}",
                    email=f"driver{i}@example.com",
                    hashed_password=hashed_password.decode('utf-8'),
                    is_driver=True
                )
                drivers.append(driver)
                db.add(driver)
            
            # Save users to get their IDs
            db.commit()
            
            # Create sample rides
            print("Creating sample rides...")
            ride1 = Ride(
                rider_id=riders[0].id,
                driver_id=drivers[0].id,
                start_location="123 Main St",
                end_location="456 Park Ave",
                status="completed",
                fare=25.50
            )
            
            ride2 = Ride(
                rider_id=riders[1].id,
                driver_id=drivers[1].id,
                start_location="789 Broadway",
                end_location="101 5th Ave",
                status="in_progress"
            )
            
            ride3 = Ride(
                rider_id=riders[2].id,
                start_location="202 Wall St",
                end_location="303 Madison Ave",
                status="requested"
            )
            
            db.add_all([ride1, ride2, ride3])
            db.commit()
            
            # Create sample payment for completed ride
            print("Creating sample payment...")
            payment = Payment(
                ride_id=ride1.id,
                amount=25.50,
                status="completed"
            )
            
            db.add(payment)
            db.commit()
            
            print("Sample data created successfully!")
        else:
            print("Database already contains data. Skipping sample data creation.")
    
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating sample data for mini-uber application...")
    create_sample_data()
