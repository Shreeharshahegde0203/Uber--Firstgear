import requests
import json

def test_ride_request():
    """Send a test ride request directly without dependencies"""
    print("\n=== Testing Ride Request API ===\n")
    
    url = "http://localhost:8000/api/ride/request"
    headers = {"Content-Type": "application/json"}
    
    # Test data
    payload = {
        "source_location": "123 Test St",
        "dest_location": "456 Destination Ave",
        "user_id": 1
    }
    
    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send request
        response = requests.post(url, json=payload, headers=headers)
        
        # Check response
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            print("\nThe ride request was successfully received by the server.")
            print("If the database connection is working, it would be stored in PostgreSQL.")
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            
            if response.status_code == 404:
                print("\nThe server is not running or the endpoint doesn't exist.")
                print("Make sure to start the server with: cd server && python run.py")
            elif response.status_code == 500:
                print("\nServer error. This might be due to database connection issues.")
                print("Check your PostgreSQL connection settings in .env file.")
            
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the server running?")
        print("\nStart the server with: cd server && python run.py")
        return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_ride_request()
