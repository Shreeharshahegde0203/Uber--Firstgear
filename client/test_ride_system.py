import argparse
import requests
import json
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL")

def send_ride_request(source, dest, user_id):
    """Send a ride request to the server and test the response"""
    print("=== Testing Ride Request API ===")
    
    # Prepare request
    url = "http://localhost:8000/api/ride/request"
    payload = {
        "source_location": source,
        "dest_location": dest,
        "user_id": user_id
    }
    headers = {"Content-Type": "application/json"}
    
    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send the request
        response = requests.post(url, json=payload, headers=headers)
        
        # Check if request was successful
        print(f"\nResponse Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            result = response.json()
            print(f"Response Data: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ Request failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        return None

def verify_database_storage(ride_id=None):
    """Verify if the ride request was stored in PostgreSQL"""
    print("\n=== Verifying PostgreSQL Database Storage ===")
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Query to get rides
        if ride_id:
            query = f"SELECT * FROM rides WHERE id = {ride_id}"
            print(f"Looking for ride with ID: {ride_id}")
        else:
            query = "SELECT * FROM rides ORDER BY created_at DESC LIMIT 5"
            print("Getting the 5 most recent rides")
        
        # Execute query
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Get column names
        colnames = [desc[0] for desc in cursor.description]
        
        # Display results
        if rows:
            print(f"\n✅ Found {len(rows)} ride(s) in the database:")
            for row in rows:
                ride_data = dict(zip(colnames, row))
                print(f"\nRide #{ride_data['id']}:")
                print(f"  - From: {ride_data['start_location']}")
                print(f"  - To: {ride_data['end_location']}")
                print(f"  - Rider ID: {ride_data['rider_id']}")
                print(f"  - Driver ID: {ride_data.get('driver_id', 'None')}")
                print(f"  - Status: {ride_data['status']}")
                print(f"  - Created at: {ride_data['created_at']}")
            
            if ride_id:
                print(f"\n✅ Confirmed: Ride #{ride_id} is stored in the PostgreSQL database!")
            return True
        else:
            print(f"\n❌ No rides found in the database")
            return False
    
    except Exception as e:
        print(f"\n❌ Database verification error: {str(e)}")
        return False
    
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def main():
    parser = argparse.ArgumentParser(description="Test Mini-Uber ride request API and verify PostgreSQL storage")
    parser.add_argument("--source", default="123 Test St", help="Source location")
    parser.add_argument("--dest", default="456 Destination Ave", help="Destination location")
    parser.add_argument("--user", type=int, default=1, help="User ID")
    parser.add_argument("--verify-only", action="store_true", help="Only verify database without sending a request")
    parser.add_argument("--ride-id", type=int, help="Specific ride ID to verify")
    
    args = parser.parse_args()
    
    if args.verify_only:
        # Just verify database storage
        verify_database_storage(args.ride_id)
    else:
        # Send request and verify database
        result = send_ride_request(args.source, args.dest, args.user)
        
        if result:
            # If request was successful, verify storage with the returned ride ID
            ride_id = result.get('id')
            verify_database_storage(ride_id)

if __name__ == "__main__":
    main()
