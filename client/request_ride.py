import requests
import json
import argparse

def request_ride(server_url, source_location, dest_location, user_id):
    """
    Send a ride request to the server API
    
    Args:
        server_url (str): Base URL of the server
        source_location (str): Starting location
        dest_location (str): Destination location
        user_id (int): ID of the requesting user
    """
    # Prepare the API endpoint
    url = f"{server_url}/api/ride/request"
    
    # Prepare the request payload
    payload = {
        "source_location": source_location,
        "dest_location": dest_location,
        "user_id": user_id
    }
    
    # Set headers for JSON content
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"\n=== Sending Ride Request ===")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send the POST request
        response = requests.post(url, json=payload, headers=headers)
        
        # Print response status and content
        print(f"\n=== Response ===")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Success! Ride request created.")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {str(e)}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Send a ride request to the Mini-Uber server")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL (default: http://localhost:8000)")
    parser.add_argument("--source", required=True, help="Source/pickup location")
    parser.add_argument("--dest", required=True, help="Destination location")
    parser.add_argument("--user", type=int, required=True, help="User ID")
    
    args = parser.parse_args()
    
    # Send the ride request
    request_ride(args.server, args.source, args.dest, args.user)
    
    # Print curl command for reference
    curl_cmd = f'''curl -X POST "{args.server}/api/ride/request" \\
    -H "Content-Type: application/json" \\
    -d '{{"source_location": "{args.source}", "dest_location": "{args.dest}", "user_id": {args.user}}}'
    '''
    
    print(f"\n=== Equivalent curl command ===")
    print(curl_cmd)
    
    # Print Postman instructions
    print(f"\n=== Postman Instructions ===")
    print("1. Open Postman")
    print("2. Create a new POST request")
    print(f"3. Enter URL: {args.server}/api/ride/request")
    print("4. Go to 'Headers' tab and add:")
    print("   Key: Content-Type, Value: application/json")
    print("5. Go to 'Body' tab, select 'raw', and choose 'JSON'")
    print("6. Enter the following JSON:")
    print(f'''{{
    "source_location": "{args.source}",
    "dest_location": "{args.dest}",
    "user_id": {args.user}
}}''')
    print("7. Click 'Send'")

if __name__ == "__main__":
    main()
