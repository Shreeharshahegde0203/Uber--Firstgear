# 🚖 Uber FirstGear# Mini-Uber Project



> **Complete documentation for the Mini Uber ride-sharing application**A simple Uber-like application with FastAPI backend and a beautiful frontend UI.



---## Project Structure



## 🚀 Quick Start```

mini-uber/

### Start the Application├── server/                # Backend code

```bash│   ├── app/

# Terminal 1: Start Server│   │   ├── api/           # API endpoints

cd server│   │   ├── core/          # Core functionality

python run.py│   │   ├── db/            # Database models and connection

│   │   └── main.py        # FastAPI application

# Terminal 2: Open All Clients│   └── run.py             # Server entry point

python start_multiple_clients.py├── client/                # Frontend code

```│   ├── index.html         # Main UI

│   ├── run_client.py      # Simple HTTP server for the client

This automatically opens:│   └── test_api.py        # Client script to test API endpoints

- 2 Driver pages├── requirements.txt       # Python dependencies

- 3 Rider pages└── .env                   # Environment variables

```

### How to Use

1. **Drivers:** Click "Go Online" button## Implementation Notes

2. **Riders:** Request a ride

3. **Drivers:** Yellow notification appears → Click "Accept"The implementation follows best practices for a modern web application:

4. Purple card shows → Click "Start Ride"

5. Click "Complete Ride" → Driver goes back online1. **Server**: FastAPI with PostgreSQL backend, well-structured with separate modules for routes, models, and business logic.



---2. **Client**: Clean HTML/CSS/JS frontend with a beautiful UI resembling Uber's design.



## 🔑 Login Credentials3. **Database**: PostgreSQL with SQLAlchemy ORM for robust data management.



### Drivers## Quick Setup

- **driver4** / password

- **driver7** / password1. **Install dependencies**:

   ```

### Riders   pip install -r requirements.txt

- **rider1** / password   ```

- **rider5** / password

- **rider6** / password2. **Configure and setup database**:

   - Database: uberclon

---   - Password: sharsha0203

   ```

## ✨ Features   python setup_database.py

   python create_sample_data.py

✅ User authentication     ```

✅ Real-time ride matching (FIFO queue)  

✅ WebSocket notifications  3. **Run the server**:

✅ 20-second offer timeout     ```

✅ Accept/Decline/Start/Complete workflow     cd server

✅ Auto-retry next driver on decline     python run.py

✅ Driver availability management     ```

✅ Interactive maps (Leaflet.js)  

✅ Persistent ride cards4. **Run the client**:

   ```

### Matching System   cd client

- **Algorithm:** FIFO queue + nearest driver   python run_client.py

- **Timeout:** 20 seconds auto-decline   ```

- **Queue:** One offer per driver at a time

- **Auto-Retry:** Next available driver5. **Test the System**:

- **Workers:** Matching, Expiry, Cleanup   ```

   # Run full system test (launches server, client, and tests database storage)

---   run_test_system.bat  # on Windows

   ./run_test_system.sh  # on Linux/Mac

## 🔧 Troubleshooting   

   # Or manually test API endpoints

### No notifications appearing?   cd client

   python test_api.py

```bash   

# Check system status   # Verify PostgreSQL database storage

python utils/check_system.py   python test_ride_system.py --verify-only

   ```

# Force drivers online

python utils/set_drivers_online.pyFor detailed setup instructions, including PostgreSQL configuration and troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

```

## User Interfaces

### Buttons not working?

- Open browser console (F12)The system includes two web interfaces:

- Look for JavaScript errors

- Check WebSocket connection1. **Rider Interface**: http://localhost:3000/index.html

   - Request rides by entering pickup and destination locations

### Other Issues   - Track ride status

- **Countdown doesn't stop:** ✅ Fixed

- **Purple card missing:** ✅ Fixed2. **Driver Interface**: http://localhost:3000/driver.html

- **Complete ride fails:** ✅ Fixed   - View incoming ride requests

   - Accept ride requests

---   - Complete rides and collect fares



## 🧪 TestingTo open the driver interface directly:

```

### Utility Scriptscd client

```bashpython run_client.py --driver

python utils/check_system.py      # System status```

python utils/check_rides.py       # View all rides

python utils/set_drivers_online.py # Force drivers online## API Endpoints

python utils/clean_rides.py       # Clean test data

```- `POST /api/ping`: Test endpoint that returns "pong" when sent "ping"

- `GET /api/health`: Health check endpoint

---- `POST /api/users`: Create a new user

- `GET /api/users/{user_id}`: Get user details

## 🏗️ Architecture- `POST /api/ride/request`: Submit a ride request with exactly these parameters:

  - `source_location`: Starting point for the ride

**Backend:** FastAPI + PostgreSQL + SQLAlchemy    - `dest_location`: Destination for the ride

**Frontend:** HTML/JavaScript + Bootstrap 5 + Leaflet.js    - `user_id`: ID of the requesting user

**Real-time:** WebSocket notifications  

**Server:** Uvicorn (ASGI)### Testing the Ride Request API



### Key Components#### Using the provided Python script:

- **Matching Engine:** `server/app/services/matching_engine.py````

- **API Routes:** `server/app/api/`python client/request_ride.py --source "123 Main St" --dest "456 Elm St" --user 1

- **Database Models:** `server/app/db/models.py````

- **Driver UI:** `client/driver.html`

- **Rider UI:** `client/index.html`#### Using curl:

```

### API Endpointscurl -X POST "http://localhost:8000/api/ride/request" \

- `POST /rides` - Create ride  -H "Content-Type: application/json" \

- `PUT /rides/{id}/accept` - Accept ride  -d '{"source_location": "123 Main St", "dest_location": "456 Elm St", "user_id": 1}'

- `PUT /rides/{id}/decline` - Decline ride```

- `PUT /rides/{id}/start` - Start ride

- `PUT /rides/{id}/complete` - Complete ride#### Using Postman:

- `PUT /users/{id}/availability` - Toggle online/offline1. Create a new POST request to `http://localhost:8000/api/ride/request`

- `WS /ws/notifications/{user_id}` - WebSocket2. Add header: `Content-Type: application/json`

3. Add body (raw JSON):

---   ```json

   {

## 📁 Project Structure     "source_location": "123 Main St",

```     "dest_location": "456 Elm St",

mini-uber/     "user_id": 1

├── server/          # Backend   }

│   ├── app/   ```

│   │   ├── api/     # API routes4. Click Send

│   │   ├── core/    # Schemas

│   │   ├── db/      # Database## Technologies Used

│   │   └── services/ # Matching engine

│   └── run.py- **Backend**: FastAPI, SQLAlchemy, PostgreSQL

├── client/          # Frontend- **Frontend**: HTML, CSS, JavaScript, Bootstrap

│   ├── driver.html- **API Testing**: Python requests library

│   ├── index.html
│   └── login.html
├── utils/           # Testing utilities
└── README.md        # This file
```

---

## 💡 Quick Commands

```bash
# Start
cd server && python run.py

# Check status
python utils/check_system.py

# Fix issues
python utils/set_drivers_online.py
python utils/clean_rides.py

# Database setup
python setup_database.py
python create_sample_data.py
```

---

## 🐛 Common Issues

**Drivers offline?** Run `python utils/set_drivers_online.py`  
**No matching?** Check server terminal logs  
**WebSocket lost?** Refresh browser page  
**No rides pending?** Run `python utils/check_rides.py`

---

## 📞 Info

**Server:** http://localhost:8000  
**Database:** PostgreSQL (miniuber)  
**Version:** 2.0 (Phase 2 Complete)  
**Updated:** October 8, 2025

---

**For issues:** Check server terminal → Check browser console (F12) → Run `python utils/check_system.py`
