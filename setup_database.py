import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database connection string from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

def setup_database():
    """
    Set up the PostgreSQL database for the mini-uber application.
    Creates the database if it doesn't exist and initializes tables.
    """
    # Extract database name from DATABASE_URL
    db_parts = DATABASE_URL.split("/")
    db_name = db_parts[-1]
    
    # Create connection string to postgres database (for creating our db)
    postgres_url = "/".join(db_parts[:-1]) + "/postgres"
    
    try:
        # Connect to postgres database
        conn = psycopg2.connect(postgres_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if our database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        # Create database if it doesn't exist
        if not exists:
            print(f"Creating database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")
        
        # Close connection to postgres database
        cursor.close()
        conn.close()
        
        print("Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    print("Setting up PostgreSQL database for mini-uber...")
    success = setup_database()
    
    if success:
        print("\nDatabase is ready!")
        print("Now you can run the server with 'python run.py' from the server directory.")
    else:
        print("\nDatabase setup failed. Please check your PostgreSQL installation and connection settings.")
        sys.exit(1)
