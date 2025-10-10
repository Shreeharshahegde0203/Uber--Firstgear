# 🚖 Uber FirstGear - Ride Sharing Application# 🚖 Uber FirstGear# Mini-Uber Project



A real-time ride-sharing platform built with FastAPI backend and vanilla JavaScript frontend, featuring automatic driver-rider matching, WebSocket notifications, and a queue-based offer system.



---> **Complete documentation for the Mini Uber ride-sharing application**A simple Uber-like application with FastAPI backend and a beautiful frontend UI.



## 📖 About The Project



**Uber FirstGear** is a simplified Uber-like application that demonstrates how modern ride-sharing platforms work. It includes:---## Project Structure



- **Real-time driver-rider matching** using a FIFO queue system

- **WebSocket notifications** for instant updates

- **Automatic offer management** with 20-second timeouts## 🚀 Quick Start```

- **Persistent UI** that updates without page refreshes

- **Multi-user testing** with parallel driver/rider sessionsmini-uber/



### Built With### Start the Application├── server/                # Backend code



**Backend:**```bash│   ├── app/

- FastAPI (Python web framework)

- PostgreSQL (Database)# Terminal 1: Start Server│   │   ├── api/           # API endpoints

- SQLAlchemy (ORM)

- WebSockets (Real-time communication)cd server│   │   ├── core/          # Core functionality

- Uvicorn (ASGI server)

python run.py│   │   ├── db/            # Database models and connection

**Frontend:**

- HTML5/CSS3/JavaScript (Vanilla JS)│   │   └── main.py        # FastAPI application

- Bootstrap 5 (UI framework)

- Leaflet.js (Interactive maps)# Terminal 2: Open All Clients│   └── run.py             # Server entry point



---python start_multiple_clients.py├── client/                # Frontend code



## 🏗️ Project Structure```│   ├── index.html         # Main UI



```│   ├── run_client.py      # Simple HTTP server for the client

mini-uber/

│This automatically opens:│   └── test_api.py        # Client script to test API endpoints

├── server/                          # Backend (FastAPI)

│   ├── app/- 2 Driver pages├── requirements.txt       # Python dependencies

│   │   ├── main.py                  # FastAPI app initialization & WebSocket endpoints

│   │   ├── config.py                # Environment configuration- 3 Rider pages└── .env                   # Environment variables

│   │   │

│   │   ├── api/                     # API endpoints (REST)```

│   │   │   ├── users.py             # User login/registration/availability

│   │   │   ├── rides.py             # Ride CRUD operations### How to Use

│   │   │   ├── ride_requests.py     # Ride creation endpoint

│   │   │   └── auth.py              # Authentication logic1. **Drivers:** Click "Go Online" button## Implementation Notes

│   │   │

│   │   ├── db/                      # Database layer2. **Riders:** Request a ride

│   │   │   ├── database.py          # SQLAlchemy engine & session

│   │   │   └── models.py            # Database table models (User, Ride)3. **Drivers:** Yellow notification appears → Click "Accept"The implementation follows best practices for a modern web application:

│   │   │

│   │   └── services/                # Business logic4. Purple card shows → Click "Start Ride"

│   │       └── matching_engine.py   # Core matching algorithm (3 workers)

│   │5. Click "Complete Ride" → Driver goes back online1. **Server**: FastAPI with PostgreSQL backend, well-structured with separate modules for routes, models, and business logic.

│   └── run.py                       # Server entry point

│

├── client/                          # Frontend (HTML/JS)

│   ├── driver.html                  # Driver interface---2. **Client**: Clean HTML/CSS/JS frontend with a beautiful UI resembling Uber's design.

│   ├── index.html                   # Rider interface

│   ├── login.html                   # Authentication page

│   └── start_multiple_clients.py    # Multi-window launcher

│## 🔑 Login Credentials3. **Database**: PostgreSQL with SQLAlchemy ORM for robust data management.

├── utils/                           # Utility scripts

│   ├── check_system.py              # System diagnostics

│   ├── set_drivers_online.py        # Force drivers online

│   ├── check_rides.py               # View all rides### Drivers## Quick Setup

│   └── clean_rides.py               # Delete test data

│- **driver4** / password

├── start_multiple_clients.py        # Launch 4 browser windows

├── setup_database.py                # Initialize database tables- **driver7** / password1. **Install dependencies**:

├── create_sample_data.py            # Create test users

└── README.md                        # This file   ```

```

### Riders   pip install -r requirements.txt

---

- **rider1** / password   ```

## 🔧 Technologies & Methods Used

- **rider5** / password

### 1. **Backend Architecture**

- **rider6** / password2. **Configure and setup database**:

#### **FastAPI Framework**

- **Async/await**: Non-blocking operations for better performance   - Database: uberclon

- **Dependency Injection**: Automatic database session management

- **Pydantic Schemas**: Request/response validation---   - Password: sharsha0203

- **CORS Middleware**: Cross-origin requests from frontend

   ```

#### **Database (PostgreSQL + SQLAlchemy ORM)**

- **SQLAlchemy Models**: Python classes mapped to database tables## ✨ Features   python setup_database.py

- **Session Management**: Connection pooling and automatic cleanup

- **Relationships**: Foreign keys between Users and Rides   python create_sample_data.py



**Key Models:**✅ User authentication     ```

```python

User Table:✅ Real-time ride matching (FIFO queue)  

  - id, username, password, email, is_driver

  - availability (online/offline)✅ WebSocket notifications  3. **Run the server**:

  - latitude, longitude (current location)

  ✅ 20-second offer timeout     ```

Ride Table:

  - id, rider_id, driver_id, status✅ Accept/Decline/Start/Complete workflow     cd server

  - pickup/dropoff locations & coordinates

  - fare, created_at, completed_at✅ Auto-retry next driver on decline     python run.py

  - Queue fields: current_offer_driver_id, offer_expires_at, declined_driver_ids

```✅ Driver availability management     ```



#### **WebSocket Communication**✅ Interactive maps (Leaflet.js)  

- **Real-time notifications**: Driver receives ride offers instantly

- **Connection Manager**: Maintains active connections per user✅ Persistent ride cards4. **Run the client**:

- **Bi-directional**: Server ↔ Client communication

   ```

### 2. **Matching Engine**

### Matching System   cd client

The heart of the system - runs 3 background workers:

- **Algorithm:** FIFO queue + nearest driver   python run_client.py

#### **Worker 1: Matching Worker (1-second interval)**

```python- **Timeout:** 20 seconds auto-decline   ```

while True:

    # Get oldest pending ride (FIFO)- **Queue:** One offer per driver at a time

    # Find available drivers (online, not busy, haven't declined)

    # Calculate nearest driver using Haversine formula- **Auto-Retry:** Next available driver5. **Test the System**:

    # Create offer and send WebSocket notification

    await asyncio.sleep(1)- **Workers:** Matching, Expiry, Cleanup   ```

```

   # Run full system test (launches server, client, and tests database storage)

**Algorithm:**

1. **FIFO Queue**: Processes oldest ride first---   run_test_system.bat  # on Windows

2. **Distance Calculation**: Haversine formula for GPS coordinates

3. **One-Offer-Per-Driver**: Enforced via `current_offer_driver_id`   ./run_test_system.sh  # on Linux/Mac

4. **Smart Filtering**: Excludes busy/offline/declined drivers

## 🔧 Troubleshooting   

#### **Worker 2: Expiry Worker (2-second interval)**

```python   # Or manually test API endpoints

while True:

    # Find offers older than 20 seconds### No notifications appearing?   cd client

    # Treat timeout as automatic decline

    # Move to next available driver   python test_api.py

    # Cancel ride if all drivers exhausted

    await asyncio.sleep(2)```bash   

```

# Check system status   # Verify PostgreSQL database storage

#### **Worker 3: Cleanup Worker (5-second interval)**

```pythonpython utils/check_system.py   python test_ride_system.py --verify-only

while True:

    # Delete completed/cancelled rides older than 24 hours   ```

    # Keeps database clean

    await asyncio.sleep(5)# Force drivers online

```

python utils/set_drivers_online.pyFor detailed setup instructions, including PostgreSQL configuration and troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

### 3. **Frontend Architecture**

```

#### **Vanilla JavaScript (No Frameworks)**

- **WebSocket Client**: Persistent connection for notifications## User Interfaces

- **Fetch API**: REST API calls (POST, PUT, GET)

- **DOM Manipulation**: Dynamic UI updates### Buttons not working?

- **Event Listeners**: Button clicks, form submissions

- Open browser console (F12)The system includes two web interfaces:

#### **State Management**

- **LocalStorage**: Store logged-in user info- Look for JavaScript errors

- **Global Variables**: Current ride state, WebSocket connection

- **UI States**: Yellow offer card → Purple active ride card- Check WebSocket connection1. **Rider Interface**: http://localhost:3000/index.html



#### **Leaflet.js Maps**   - Request rides by entering pickup and destination locations

- **Interactive Maps**: Display pickup/dropoff locations

- **Markers**: Show driver and rider positions### Other Issues   - Track ride status

- **Routing**: Visual path between locations

- **Countdown doesn't stop:** ✅ Fixed

### 4. **Key Design Patterns**

- **Purple card missing:** ✅ Fixed2. **Driver Interface**: http://localhost:3000/driver.html

#### **Observer Pattern**

- WebSocket notifications push updates to clients- **Complete ride fails:** ✅ Fixed   - View incoming ride requests

- No polling needed - instant updates

   - Accept ride requests

#### **Queue Pattern**

- FIFO processing of ride requests---   - Complete rides and collect fares

- Fair distribution to drivers



#### **State Machine**

```## 🧪 TestingTo open the driver interface directly:

Ride Status Flow:

pending → offering → accepted → in_progress → completed```

                   ↘ declined → offering (next driver)

                             ↘ cancelled (no drivers)### Utility Scriptscd client

```

```bashpython run_client.py --driver

#### **Worker Pattern**

- Background async tasks run independentlypython utils/check_system.py      # System status```

- Non-blocking - doesn't freeze server

python utils/check_rides.py       # View all rides

### 5. **Database Techniques**

python utils/set_drivers_online.py # Force drivers online## API Endpoints

#### **SQLAlchemy ORM**

```pythonpython utils/clean_rides.py       # Clean test data

# Python code translates to SQL

user = db.query(User).filter_by(username="john").first()```- `POST /api/ping`: Test endpoint that returns "pong" when sent "ping"

# Becomes: SELECT * FROM users WHERE username='john' LIMIT 1

```- `GET /api/health`: Health check endpoint



#### **Relationships**---- `POST /api/users`: Create a new user

```python

class Ride:- `GET /api/users/{user_id}`: Get user details

    rider_id = Column(Integer, ForeignKey('users.id'))

    driver_id = Column(Integer, ForeignKey('users.id'))## 🏗️ Architecture- `POST /api/ride/request`: Submit a ride request with exactly these parameters:

```

  - `source_location`: Starting point for the ride

#### **Transactions**

```python**Backend:** FastAPI + PostgreSQL + SQLAlchemy    - `dest_location`: Destination for the ride

db.add(ride)

db.commit()  # Atomic - all or nothing**Frontend:** HTML/JavaScript + Bootstrap 5 + Leaflet.js    - `user_id`: ID of the requesting user

```

**Real-time:** WebSocket notifications  

### 6. **Real-Time Features**

**Server:** Uvicorn (ASGI)### Testing the Ride Request API

#### **WebSocket Protocol**

```javascript

// Client connects

const ws = new WebSocket('ws://localhost:8000/ws/notifications/4');### Key Components#### Using the provided Python script:



// Receive notifications- **Matching Engine:** `server/app/services/matching_engine.py````

ws.onmessage = (event) => {

    const data = JSON.parse(event.data);- **API Routes:** `server/app/api/`python client/request_ride.py --source "123 Main St" --dest "456 Elm St" --user 1

    if (data.type === 'ride_offer_received') {

        displayOffer(data.ride);- **Database Models:** `server/app/db/models.py````

    }

};- **Driver UI:** `client/driver.html`

```

- **Rider UI:** `client/index.html`#### Using curl:

#### **Async/Await Pattern**

```python```

# Non-blocking operations

async def create_offer(ride_id, driver_id):### API Endpointscurl -X POST "http://localhost:8000/api/ride/request" \

    await send_notification(driver_id, ride)

    # Doesn't block other requests- `POST /rides` - Create ride  -H "Content-Type: application/json" \

```

- `PUT /rides/{id}/accept` - Accept ride  -d '{"source_location": "123 Main St", "dest_location": "456 Elm St", "user_id": 1}'

### 7. **Testing Architecture**

- `PUT /rides/{id}/decline` - Decline ride```

#### **Multi-Client System**

- 4 separate HTTP servers (ports 3001-3004)- `PUT /rides/{id}/start` - Start ride

- Each simulates different user session

- Tests concurrent ride scenarios- `PUT /rides/{id}/complete` - Complete ride#### Using Postman:



#### **Utility Scripts**- `PUT /users/{id}/availability` - Toggle online/offline1. Create a new POST request to `http://localhost:8000/api/ride/request`

- `check_system.py`: View system state

- `set_drivers_online.py`: Reset driver availability- `WS /ws/notifications/{user_id}` - WebSocket2. Add header: `Content-Type: application/json`

- Clean separation of concerns

3. Add body (raw JSON):

---

---   ```json

## 🚀 Getting Started

   {

### Prerequisites

## 📁 Project Structure     "source_location": "123 Main St",

- Python 3.10+

- PostgreSQL database```     "dest_location": "456 Elm St",

- Web browser (Chrome/Firefox recommended)

mini-uber/     "user_id": 1

### Installation

├── server/          # Backend   }

1. **Clone the repository**

```bash│   ├── app/   ```

git clone https://github.com/Shreeharshahegde0203/Uber--Firstgear.git

cd Uber--Firstgear/mini-uber│   │   ├── api/     # API routes4. Click Send

```

│   │   ├── core/    # Schemas

2. **Install dependencies**

```bash│   │   ├── db/      # Database## Technologies Used

pip install -r requirements.txt

```│   │   └── services/ # Matching engine



3. **Setup database**│   └── run.py- **Backend**: FastAPI, SQLAlchemy, PostgreSQL

```bash

python setup_database.py├── client/          # Frontend- **Frontend**: HTML, CSS, JavaScript, Bootstrap

python create_sample_data.py

```│   ├── driver.html- **API Testing**: Python requests library



4. **Start the server**│   ├── index.html

```bash│   └── login.html

cd server├── utils/           # Testing utilities

python run.py└── README.md        # This file

``````



5. **Launch clients**---

```bash

# In a new terminal## 💡 Quick Commands

python start_multiple_clients.py

``````bash

# Start

### Login Credentialscd server && python run.py



**Drivers:**# Check status

- driver4 / passwordpython utils/check_system.py

- driver7 / password

# Fix issues

**Riders:**python utils/set_drivers_online.py

- rider1 / passwordpython utils/clean_rides.py

- rider5 / password

- rider6 / password# Database setup

python setup_database.py

---python create_sample_data.py

```

## 📊 How It Works

---

### Complete Flow Example

## 🐛 Common Issues

```

1. RIDER REQUESTS RIDE**Drivers offline?** Run `python utils/set_drivers_online.py`  

   └─> POST /api/rides**No matching?** Check server terminal logs  

       └─> Creates ride in database (status: pending)**WebSocket lost?** Refresh browser page  

**No rides pending?** Run `python utils/check_rides.py`

2. MATCHING WORKER (1 second later)

   └─> Finds pending ride---

   └─> Queries available drivers

   └─> Calculates nearest using Haversine formula## 📞 Info

   └─> Creates offer in database

   └─> Sends WebSocket notification to driver**Server:** http://localhost:8000  

**Database:** PostgreSQL (miniuber)  

3. DRIVER RECEIVES NOTIFICATION**Version:** 2.0 (Phase 2 Complete)  

   └─> Yellow card appears on screen**Updated:** October 8, 2025

   └─> 20-second countdown starts

   └─> Driver clicks "Accept" or "Decline"---



4A. IF DRIVER ACCEPTS**For issues:** Check server terminal → Check browser console (F12) → Run `python utils/check_system.py`

    └─> PUT /api/rides/{id}/accept
        └─> Updates ride status to "accepted"
        └─> Marks driver as busy
        └─> Notifies rider via WebSocket
        └─> Purple persistent card appears

4B. IF DRIVER DECLINES (or timeout)
    └─> PUT /api/rides/{id}/decline
        └─> Adds driver to declined list
        └─> Matching worker finds next driver
        └─> Repeats from step 2

5. START RIDE
   └─> PUT /api/rides/{id}/start
       └─> Updates status to "in_progress"

6. COMPLETE RIDE
   └─> PUT /api/rides/{id}/complete
       └─> Updates status to "completed"
       └─> Sets driver back to available
       └─> Driver can accept new rides
```

---

## 🔑 Key Features

### 1. **Automatic Matching**
- FIFO queue ensures fairness
- Distance-based driver selection
- No manual intervention needed

### 2. **Offer System**
- 20-second timeout per driver
- One offer at a time per driver
- Automatic retry with next driver

### 3. **Real-Time Updates**
- WebSocket notifications (no polling)
- Instant UI updates
- Bi-directional communication

### 4. **Persistent UI**
- Ride cards stay visible
- No page refresh needed
- State managed in JavaScript

### 5. **Queue Management**
- FIFO order processing
- Declined driver tracking
- Prevents duplicate offers

---

## 🧪 Testing

### Manual Testing
1. Start server and multi-client
2. Login as driver → Go Online
3. Login as rider → Request ride
4. Watch notification appear
5. Accept → Start → Complete

### Check System Status
```bash
python utils/check_system.py
```

### Force Drivers Online
```bash
python utils/set_drivers_online.py
```

### Clean Test Data
```bash
python utils/clean_rides.py
```

---

## 🐛 Troubleshooting

**No notifications?**
- Run `python utils/check_system.py`
- Check if drivers are online
- Run `python utils/set_drivers_online.py`

**Buttons not working?**
- Open browser console (F12)
- Check for JavaScript errors
- Verify WebSocket connection

**Server not starting?**
- Check if port 8000 is available
- Verify PostgreSQL is running
- Check database credentials in `.env`

---

## 📚 Learning Outcomes

This project demonstrates:

✅ **Backend Development**: FastAPI, async/await, WebSockets  
✅ **Database Design**: SQLAlchemy ORM, relationships, transactions  
✅ **Real-Time Systems**: WebSocket communication, push notifications  
✅ **Algorithm Design**: FIFO queue, distance calculation, state machines  
✅ **Frontend Development**: Vanilla JavaScript, DOM manipulation, API integration  
✅ **System Architecture**: Worker patterns, background tasks, separation of concerns  
✅ **Testing**: Multi-user scenarios, concurrent operations  

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This is an educational project created for learning purposes.

---

## 👨‍💻 Author

**Shree Harsha Hegde**  
GitHub: [@Shreeharshahegde0203](https://github.com/Shreeharshahegde0203)

---

## 🙏 Acknowledgments

- FastAPI documentation
- PostgreSQL community
- Leaflet.js for maps
- Bootstrap for UI components

---

**Version:** 2.0 (Phase 2 Complete)  
**Last Updated:** October 10, 2025
