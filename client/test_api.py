import requests
import json
import sys

def test_ping_endpoint(base_url):
    """
    Test the ping endpoint with a valid request.
    """
    endpoint = f"{base_url}/api/ping"
    headers = {"Content-Type": "application/json"}
    payload = {"data": "ping"}
    
    try:
        # Using correct key for the payload
        payload = {"data": "ping"}
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=4)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False

def test_health_endpoint(base_url):
    """
    Test the health endpoint.
    """
    endpoint = f"{base_url}/api/health"
    
    try:
        response = requests.get(endpoint)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=4)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False

def test_create_user(base_url):
    """
    Test user creation endpoint.
    """
    endpoint = f"{base_url}/api/users"
    headers = {"Content-Type": "application/json"}
    
    # Generate a unique username
    import random
    username = f"user_{random.randint(1000, 9999)}"
    
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "password123",
        "is_driver": False
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=4)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False

def main():
    """
    Main function to run all tests.
    """
    if len(sys.argv) < 2:
        base_url = "http://localhost:8000"
        print(f"No base URL provided, using default: {base_url}")
    else:
        base_url = sys.argv[1]
        print(f"Using base URL: {base_url}")
    
    # Run tests
    print("\n=== Testing Ping Endpoint ===")
    ping_result = test_ping_endpoint(base_url)
    
    print("\n=== Testing Health Endpoint ===")
    health_result = test_health_endpoint(base_url)
    
    print("\n=== Testing User Creation ===")
    user_result = test_create_user(base_url)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Ping Endpoint: {'SUCCESS' if ping_result else 'FAILED'}")
    print(f"Health Endpoint: {'SUCCESS' if health_result else 'FAILED'}")
    print(f"User Creation: {'SUCCESS' if user_result else 'FAILED'}")

if __name__ == "__main__":
    main()
