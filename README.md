# Mini-Uber Project

A simple Uber-like application with FastAPI backend and a beautiful frontend UI.

## Project Structure

```
mini-uber/
├── server/                # Backend code
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core functionality
│   │   ├── db/            # Database models and connection
│   │   └── main.py        # FastAPI application
│   └── run.py             # Server entry point
├── client/                # Frontend code
│   ├── index.html         # Main UI
│   ├── run_client.py      # Simple HTTP server for the client
│   └── test_api.py        # Client script to test API endpoints
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables
```

## Implementation Notes

The implementation follows best practices for a modern web application:

1. **Server**: FastAPI with PostgreSQL backend, well-structured with separate modules for routes, models, and business logic.

2. **Client**: Clean HTML/CSS/JS frontend with a beautiful UI resembling Uber's design.

3. **Database**: PostgreSQL with SQLAlchemy ORM for robust data management.

## Quick Setup

1. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Configure and setup database**:
   - Database: uberclon
   - Password: sharsha0203
   ```
   python setup_database.py
   python create_sample_data.py
   ```

3. **Run the server**:
   ```
   cd server
   python run.py
   ```

4. **Run the client**:
   ```
   cd client
   python run_client.py
   ```

5. **Test the System**:
   ```
   # Run full system test (launches server, client, and tests database storage)
   run_test_system.bat  # on Windows
   ./run_test_system.sh  # on Linux/Mac
   
   # Or manually test API endpoints
   cd client
   python test_api.py
   
   # Verify PostgreSQL database storage
   python test_ride_system.py --verify-only
   ```

For detailed setup instructions, including PostgreSQL configuration and troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## User Interfaces

The system includes two web interfaces:

1. **Rider Interface**: http://localhost:3000/index.html
   - Request rides by entering pickup and destination locations
   - Track ride status

2. **Driver Interface**: http://localhost:3000/driver.html
   - View incoming ride requests
   - Accept ride requests
   - Complete rides and collect fares

To open the driver interface directly:
```
cd client
python run_client.py --driver
```

## API Endpoints

- `POST /api/ping`: Test endpoint that returns "pong" when sent "ping"
- `GET /api/health`: Health check endpoint
- `POST /api/users`: Create a new user
- `GET /api/users/{user_id}`: Get user details
- `POST /api/ride/request`: Submit a ride request with exactly these parameters:
  - `source_location`: Starting point for the ride
  - `dest_location`: Destination for the ride
  - `user_id`: ID of the requesting user

### Testing the Ride Request API

#### Using the provided Python script:
```
python client/request_ride.py --source "123 Main St" --dest "456 Elm St" --user 1
```

#### Using curl:
```
curl -X POST "http://localhost:8000/api/ride/request" \
  -H "Content-Type: application/json" \
  -d '{"source_location": "123 Main St", "dest_location": "456 Elm St", "user_id": 1}'
```

#### Using Postman:
1. Create a new POST request to `http://localhost:8000/api/ride/request`
2. Add header: `Content-Type: application/json`
3. Add body (raw JSON):
   ```json
   {
     "source_location": "123 Main St",
     "dest_location": "456 Elm St",
     "user_id": 1
   }
   ```
4. Click Send

## Technologies Used

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **API Testing**: Python requests library
