# 🎓 Uber First Gear - Viva Preparation Guide

## 📚 Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Potential Viva Questions & Answers](#potential-viva-questions--answers)
4. [Key Concepts Explained](#key-concepts-explained)
5. [Architecture Diagram](#architecture-diagram)
6. [Quick Reference Cheat Sheet](#quick-reference-cheat-sheet)

---

## 🚗 Project Overview

**Uber First Gear** is a driving lesson booking marketplace that connects students who want to learn driving with certified instructors through a competitive bidding system.

### Core Features:

| Feature | Description |
|---------|-------------|
| **Lesson Booking** | Students book lessons with location, date, time, duration |
| **Bidding System** | Instructors bid on lessons, students choose the best offer |
| **Real-time Notifications** | WebSocket-based instant updates |
| **Payment Integration** | Razorpay for UPI/Card payments |
| **AI Quiz** | Daily driving quiz with coin rewards |
| **Location-based Matching** | Prioritizes nearby instructors (5km → expanding) |

---

## 🛠️ Technology Stack

### Backend

| Technology | Purpose | Why We Used It |
|------------|---------|----------------|
| **Python** | Programming Language | Easy to read, large ecosystem, great for rapid development |
| **FastAPI** | Web Framework | Async support, automatic API docs, type hints, high performance |
| **PostgreSQL** | Database | ACID compliance, relational data, complex queries, data integrity |
| **SQLAlchemy** | ORM | Python-SQL mapping, prevents SQL injection, easier queries |
| **WebSockets** | Real-time Communication | Bi-directional, low latency notifications |
| **Uvicorn** | ASGI Server | Async server for FastAPI, production-ready |

### Frontend

| Technology | Purpose | Why We Used It |
|------------|---------|----------------|
| **HTML5** | Structure | Semantic markup, accessibility |
| **CSS3** | Styling | Animations, responsive design, flexbox/grid |
| **JavaScript (Vanilla)** | Interactivity | No framework overhead, direct DOM manipulation |
| **WebSocket API** | Real-time Updates | Native browser support, persistent connection |

### External Services

| Service | Purpose | Why We Used It |
|---------|---------|----------------|
| **Razorpay** | Payments | Indian payment gateway, UPI support, easy integration |
| **Nominatim/OSM** | Location Autocomplete | Free, no API key needed, good India coverage |

---

## ❓ Potential Viva Questions & Answers

### 1. DATABASE QUESTIONS

#### Q1: Why did you use PostgreSQL instead of MongoDB (SQL vs NoSQL)?

**Answer:**
```
We chose PostgreSQL (SQL/Relational) because:

1. **Structured Data**: Our data has clear relationships:
   - Users → Bookings (one-to-many)
   - Bookings → Bids (one-to-many)
   - Tutors → Users (one-to-one)
   
2. **ACID Compliance**: 
   - Atomicity: Payment + Booking update must happen together
   - Consistency: Bid rankings must be accurate
   - Isolation: Multiple bids shouldn't conflict
   - Durability: Data persists after crashes

3. **Complex Queries**: 
   - JOIN operations (get booking with tutor details)
   - Aggregations (total earnings, bid counts)
   - Filtering (lessons by status, date range)

4. **Data Integrity**:
   - Foreign keys prevent orphan records
   - Constraints ensure valid data (e.g., bid_amount > 0)

MongoDB would be better for:
- Unstructured/varying data schemas
- High write throughput (logs, analytics)
- Document-based storage (blog posts, comments)
```

---

#### Q2: What is an ORM? Why use SQLAlchemy?

**Answer:**
```
ORM = Object Relational Mapping

It maps Python classes to database tables:

# Python Class (Model)
class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)

# Automatically creates SQL:
# CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR, email VARCHAR)

Benefits of SQLAlchemy:
1. Write Python instead of raw SQL
2. Prevents SQL injection attacks
3. Database-agnostic (switch PostgreSQL → MySQL easily)
4. Automatic query building
5. Relationship management (foreign keys, joins)

Example:
# Instead of: SELECT * FROM users WHERE id = 5
user = db.query(User).filter(User.id == 5).first()
```

---

#### Q3: Explain the database schema/relationships

**Answer:**
```
We have 4 main tables:

1. USERS (id, username, email, password, role, coins)
   ↓ one-to-one
2. TUTORS (id, user_id, license_no, experience, hourly_rate, rating)
   
1. USERS 
   ↓ one-to-many
3. LESSON_BOOKINGS (id, student_id, tutor_id, status, lesson_type, date, time)
   ↓ one-to-many
4. LESSON_BIDS (id, booking_id, tutor_id, bid_amount, status, bid_rank)

Relationships:
- A User can have many LessonBookings (as student)
- A LessonBooking can have many LessonBids
- A Tutor belongs to one User
- A Tutor can have many LessonBids
```

---

### 2. BACKEND QUESTIONS

#### Q4: Why FastAPI over Flask or Django?

**Answer:**
```
FastAPI advantages:

1. **Async/Await Support**: 
   - Handle many concurrent requests
   - Essential for WebSockets and real-time features
   
2. **Automatic API Documentation**:
   - Swagger UI at /docs
   - No extra work needed

3. **Type Hints & Validation**:
   - Pydantic models validate input automatically
   - Catches errors before they reach database

4. **Performance**:
   - One of the fastest Python frameworks
   - Comparable to Node.js and Go

Flask: Simpler but no async, no auto-validation
Django: Full-featured but heavier, slower for APIs
```

---

#### Q5: Explain the bidding flow/algorithm

**Answer:**
```
BIDDING FLOW:

1. STUDENT CREATES BOOKING
   └─> Status: BIDDING_OPEN
   └─> bidding_closes_at = now + 15 minutes

2. NOTIFY NEARBY TUTORS (Location-based priority)
   └─> Calculate distance from lesson location
   └─> Sort tutors by distance (nearest first)
   └─> Start with 5km radius, expand every 5 minutes
   └─> Send WebSocket notification to each tutor

3. TUTORS PLACE BIDS
   └─> Each bid stored with tutor_id, amount
   └─> Bids ranked by amount (lowest = rank 1)
   └─> booking.total_bids incremented
   └─> Student notified of new bid

4. RANKING ALGORITHM
   └─> Query all active bids for booking
   └─> Sort by bid_amount ascending
   └─> Assign rank 1, 2, 3...
   └─> Update bid_rank in database

5. STUDENT SELECTS TUTOR
   └─> Status: TUTOR_SELECTED
   └─> Selected tutor notified
   └─> Other tutors notified (rejected)

6. TUTOR ACCEPTS → PAYMENT → CONFIRMED → IN_PROGRESS → COMPLETED
```

---

#### Q6: How does the WebSocket notification system work?

**Answer:**
```
WebSocket = Persistent bi-directional connection

Traditional HTTP:
Client ──request──> Server
Client <──response── Server
(Connection closes)

WebSocket:
Client <────────────> Server
(Connection stays open, both can send anytime)

Our Implementation:

1. CONNECTION MANAGER (server/app/main.py)
   - Stores active connections: {user_id: websocket}
   - Methods: connect(), disconnect(), send_to_user()

2. CLIENT CONNECTS
   const ws = new WebSocket(`ws://localhost:8000/ws/notifications/${userId}`);
   
3. SERVER STORES CONNECTION
   user_connections[user_id] = websocket

4. SENDING NOTIFICATIONS
   await manager.send_to_user(user_id, {
       "type": "new_bid_received",
       "booking_id": 5,
       "message": "New bid received!"
   })

5. CLIENT RECEIVES & HANDLES
   ws.onmessage = (event) => {
       const data = JSON.parse(event.data);
       if (data.type === "new_bid_received") {
           showNotification(data.message);
           refreshBookings();
       }
   }

Use Cases:
- New bid notification to student
- Tutor selected notification
- Lesson started/completed alerts
```

---

#### Q7: How do you handle authentication?

**Answer:**
```
We use Session-based authentication with localStorage:

1. LOGIN FLOW:
   - User enters username/password
   - Server validates against database (hashed password)
   - Server returns user object
   - Frontend stores in localStorage

2. STORAGE:
   localStorage.setItem('user', JSON.stringify(userData));

3. PROTECTED REQUESTS:
   - Frontend reads user from localStorage
   - Sends user_id with API requests
   - Server validates user exists

4. LOGOUT:
   localStorage.removeItem('user');

For production, we'd use:
- JWT (JSON Web Tokens) for stateless auth
- HTTP-only cookies for security
- Token refresh mechanism
```

---

### 3. FRONTEND QUESTIONS

#### Q8: Why vanilla JavaScript instead of React/Vue?

**Answer:**
```
Reasons for Vanilla JS:

1. **No Build Step**: 
   - Direct browser execution
   - Faster development for small projects
   
2. **Learning Purpose**:
   - Understand core concepts first
   - No framework magic hiding logic

3. **Performance**:
   - No framework overhead
   - Smaller file sizes

4. **Simplicity**:
   - Fewer dependencies
   - Easier deployment (just HTML/CSS/JS)

When to use React/Vue:
- Large applications with complex state
- Team collaboration (component reusability)
- Single Page Applications (SPA)
```

---

#### Q9: How does the location autocomplete work?

**Answer:**
```
We use Nominatim (OpenStreetMap's geocoding service):

1. USER TYPES ADDRESS
   └─> Input event triggers with 300ms debounce

2. DEBOUNCE (prevents too many API calls)
   let timeout;
   function debounce(func, delay) {
       clearTimeout(timeout);
       timeout = setTimeout(func, delay);
   }

3. API CALL TO NOMINATIM
   fetch(`https://nominatim.openstreetmap.org/search?
       format=json&
       q=${query}&
       countrycodes=in&  // India only
       limit=5`)

4. DISPLAY SUGGESTIONS
   └─> Show dropdown with location names
   └─> Each item has: display_name, lat, lon

5. USER SELECTS LOCATION
   └─> Fill input with display_name
   └─> Store lat/lon in hidden fields
   └─> Close dropdown

Benefits:
- Free (no API key needed)
- Good India coverage
- Returns coordinates for distance calculation
```

---

#### Q10: Explain the CSS animations used

**Answer:**
```
We use CSS @keyframes for animations:

1. FADE IN ANIMATION
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.element { animation: fadeIn 0.6s ease-out; }

2. FLOATING ANIMATION (for promo image)
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
.promo-image { animation: float 3s ease-in-out infinite; }

3. PULSE ANIMATION (for live badge)
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
}
.live-dot { animation: pulse 2s infinite; }

4. HOVER TRANSITIONS
.card {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
```

---

### 4. API & INTEGRATION QUESTIONS

#### Q11: How does Razorpay payment integration work?

**Answer:**
```
PAYMENT FLOW:

1. CREATE ORDER (Backend)
   POST /api/lessons/create-payment
   └─> razorpay.orders.create({
         amount: 60000,  // ₹600 in paise
         currency: "INR"
       })
   └─> Returns order_id

2. OPEN CHECKOUT (Frontend)
   const options = {
       key: "RAZORPAY_KEY",
       amount: 60000,
       order_id: order_id,
       handler: function(response) {
           // Payment successful
           verifyPayment(response);
       }
   };
   new Razorpay(options).open();

3. VERIFY PAYMENT (Backend)
   POST /api/lessons/verify-payment
   └─> Verify signature using HMAC SHA256
   └─> signature = HMAC_SHA256(order_id + "|" + payment_id, secret)
   └─> If valid, update booking status

4. CONFIRM BOOKING
   └─> payment_status = "completed"
   └─> booking status = "CONFIRMED"
   └─> Notify tutor
```

---

#### Q12: How does the Quiz system work?

**Answer:**
```
QUIZ FLOW:

1. QUESTION BANK
   - 20+ curated driving questions stored in Python
   - Each has: question, 4 options, correct_answer, explanation

2. DAILY QUIZ GENERATION
   - Select 5 random questions from bank
   - Store active quiz in memory: {user_id: questions}
   - Return questions WITHOUT correct answers

3. ANSWER CHECKING
   POST /api/quiz/check-answer
   - Receive: user_id, question_id, answer_index
   - Compare with correct answer
   - Return: correct (bool), correct_answer, explanation

4. QUIZ SUBMISSION
   POST /api/quiz/submit
   - Calculate score
   - If score >= 80% (4/5): Award 10 coins
   - Update user.coins in database
   - Mark last_quiz_date to prevent retake

5. COIN REWARD SYSTEM
   - 10 coins = ₹1 discount
   - Coins stored in user.coins field
   - Can redeem during booking payment
```

---

### 5. ARCHITECTURE & DESIGN QUESTIONS

#### Q13: Explain the MVC/Project architecture

**Answer:**
```
Our project follows a layered architecture:

mini-uber/
├── server/                 # BACKEND
│   └── app/
│       ├── main.py        # Entry point, routes mounting
│       ├── api/           # CONTROLLERS (handle requests)
│       │   ├── auth.py    # Login/Register endpoints
│       │   ├── lessons.py # Booking/Bidding endpoints
│       │   ├── tutors.py  # Tutor management
│       │   └── quiz.py    # Quiz endpoints
│       ├── db/            # MODELS (data layer)
│       │   ├── database.py    # DB connection
│       │   └── models.py      # SQLAlchemy models
│       └── services/      # BUSINESS LOGIC
│           ├── matching_engine.py
│           └── bidding_engine.py
│
├── client/                # FRONTEND (VIEW)
│   ├── index.html        # Student homepage
│   ├── driver.html       # Driver homepage
│   ├── student-*.html    # Student pages
│   └── tutor-*.html      # Tutor pages

Data Flow:
Client → API Endpoint → Database → Response → Client
         (Controller)    (Model)
```

---

#### Q14: How do you handle concurrent bids?

**Answer:**
```
CONCURRENCY HANDLING:

1. DATABASE TRANSACTIONS
   with db.begin():
       # All operations in single transaction
       bid = LessonBid(...)
       db.add(bid)
       booking.total_bids += 1
       # Either all succeed or all rollback

2. ROW-LEVEL LOCKING (if needed)
   booking = db.query(LessonBooking)\
       .filter(id == booking_id)\
       .with_for_update()\  # Locks the row
       .first()

3. BID RANKING
   - Recalculated after each new bid
   - Uses ORDER BY bid_amount ASC
   - Atomic update of all bid_ranks

4. STATUS CHECKS
   - Verify booking status is BIDDING_OPEN
   - Verify bidding window not expired
   - Reject duplicate bids from same tutor
```

---

#### Q15: How would you scale this application?

**Answer:**
```
SCALING STRATEGIES:

1. HORIZONTAL SCALING (Multiple Servers)
   - Run multiple FastAPI instances
   - Load balancer distributes requests
   - Stateless design (no server-side sessions)

2. DATABASE SCALING
   - Read replicas for queries
   - Connection pooling (already using)
   - Indexing on frequently queried columns

3. CACHING
   - Redis for session storage
   - Cache quiz questions (daily)
   - Cache tutor listings

4. WEBSOCKET SCALING
   - Redis Pub/Sub for multi-server WebSocket
   - Each server subscribes to channels
   - Messages broadcast across all instances

5. MICROSERVICES (Future)
   - Separate services: Auth, Booking, Payment, Quiz
   - Independent scaling per service
   - Message queues for async communication
```

---

## 🔑 Key Concepts Explained

### 1. REST API
```
REST = Representational State Transfer

Principles:
- Stateless (no server-side session)
- Resource-based URLs (/api/lessons, /api/users)
- HTTP methods define actions:
  GET    = Read
  POST   = Create
  PUT    = Update (full)
  PATCH  = Update (partial)
  DELETE = Delete

Example:
GET    /api/lessons          → List all lessons
POST   /api/lessons          → Create new lesson
GET    /api/lessons/5        → Get lesson #5
PUT    /api/lessons/5        → Update lesson #5
DELETE /api/lessons/5        → Delete lesson #5
```

---

### 2. CORS (Cross-Origin Resource Sharing)
```
Problem: Browser blocks requests to different domains
Solution: Server sends headers allowing cross-origin requests

Our Setup:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all domains
    allow_methods=["*"],      # Allow all HTTP methods
    allow_headers=["*"],      # Allow all headers
)

In production: Restrict to specific domains
allow_origins=["https://uberfirstgear.com"]
```

---

### 3. Async/Await
```
Synchronous (blocking):
def get_data():
    result1 = database_query()    # Waits 100ms
    result2 = api_call()          # Waits 200ms
    return result1, result2       # Total: 300ms

Asynchronous (non-blocking):
async def get_data():
    task1 = asyncio.create_task(database_query())
    task2 = asyncio.create_task(api_call())
    result1, result2 = await asyncio.gather(task1, task2)
    return result1, result2       # Total: 200ms (parallel)

Benefits:
- Handle more concurrent requests
- Better resource utilization
- Essential for real-time features
```

---

### 4. Database Indexing
```
Without Index: Full table scan O(n)
With Index: B-tree lookup O(log n)

Example:
# Slow (scans all bookings)
SELECT * FROM lesson_bookings WHERE student_id = 5;

# Fast (uses index)
CREATE INDEX idx_student_id ON lesson_bookings(student_id);
SELECT * FROM lesson_bookings WHERE student_id = 5;

We index:
- Foreign keys (student_id, tutor_id, booking_id)
- Frequently filtered columns (status, lesson_date)
```

---

### 5. Password Hashing
```
NEVER store plain text passwords!

We use bcrypt hashing:
import bcrypt

# Registration
password = "user123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
# Stored: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G4R0A

# Login
if bcrypt.checkpw(input_password.encode(), stored_hash):
    print("Login successful")

Why bcrypt?
- One-way (can't decrypt)
- Salted (same password = different hash)
- Slow by design (prevents brute force)
```

---

### 6. Haversine Formula (Distance Calculation)
```
Used to calculate distance between two GPS coordinates:

def calculate_distance_km(lat1, lng1, lat2, lng2):
    R = 6371  # Earth's radius in km
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    # Haversine formula
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c  # Distance in km

Used for:
- Finding nearby tutors
- Expanding search radius (5km → 7km → 9km)
- Sorting tutors by proximity
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Student    │  │   Driver     │  │    Quiz      │              │
│  │   Pages      │  │   Pages      │  │    Page      │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └────────────┬────┴────────────────┘                       │
│                      │                                              │
│              ┌───────▼───────┐                                      │
│              │  JavaScript   │                                      │
│              │  (API calls)  │                                      │
│              └───────┬───────┘                                      │
└──────────────────────┼──────────────────────────────────────────────┘
                       │
          HTTP/REST    │    WebSocket
          ─────────────┼─────────────
                       │
┌──────────────────────┼──────────────────────────────────────────────┐
│                      │         SERVER (FastAPI)                     │
│              ┌───────▼───────┐                                      │
│              │    Uvicorn    │                                      │
│              │  ASGI Server  │                                      │
│              └───────┬───────┘                                      │
│                      │                                              │
│    ┌─────────────────┼─────────────────┐                           │
│    │                 │                 │                            │
│    ▼                 ▼                 ▼                            │
│ ┌──────┐        ┌──────┐        ┌──────────┐                       │
│ │ Auth │        │Lessons│       │ WebSocket │                       │
│ │ API  │        │  API  │       │  Manager  │                       │
│ └──┬───┘        └──┬───┘        └─────┬────┘                       │
│    │               │                  │                             │
│    └───────────────┼──────────────────┘                            │
│                    │                                                │
│            ┌───────▼───────┐                                        │
│            │  SQLAlchemy   │                                        │
│            │     ORM       │                                        │
│            └───────┬───────┘                                        │
└────────────────────┼────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Users   │  │  Tutors  │  │ Bookings │  │   Bids   │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
└────────────────────────────────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌────────┐    ┌──────────┐    ┌──────────┐
│Razorpay│    │ Quiz     │    │Nominatim │
│Payment │    │ System   │    │  Maps    │
└────────┘    └──────────┘    └──────────┘
```

---

## 📋 Quick Reference Cheat Sheet

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register` | Create new user |
| POST | `/api/auth/login` | User login |
| POST | `/api/lessons/request` | Create booking |
| POST | `/api/lessons/bid` | Place bid |
| POST | `/api/lessons/select-tutor` | Select winning bid |
| GET | `/api/lessons/student/{id}` | Get student's bookings |
| GET | `/api/quiz/daily/{id}` | Get quiz questions |
| POST | `/api/quiz/check-answer` | Check single answer |
| POST | `/api/quiz/submit` | Submit quiz answers |

---

### Booking Status Flow
```
BIDDING_OPEN → TUTOR_SELECTED → CONFIRMED → IN_PROGRESS → COMPLETED
                    ↓
               (rejected bids)
```

---

### Key Files

| File | Purpose |
|------|---------|
| `server/app/main.py` | App entry, middleware, WebSocket, routes |
| `server/app/db/models.py` | Database table definitions |
| `server/app/api/lessons.py` | Booking/bidding logic |
| `server/app/api/quiz.py` | Quiz system |
| `client/index.html` | Student landing page |
| `client/driver.html` | Instructor landing page |
| `client/student-book-lesson.html` | Lesson booking form |
| `client/student-bidding.html` | View bids on booking |

---

### Environment Variables
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
```

---

### Common Terminal Commands
```bash
# Start server
python -m uvicorn server.app.main:app --reload --port 8000

# Install dependencies
pip install -r requirements.txt

# Database migration
python migrate_db.py
```

---

## 💡 Tips for Viva

1. **Start with overview**: "Uber First Gear is a marketplace connecting driving students with instructors through competitive bidding"

2. **Use analogies**: "Like Uber, but for learning to drive"

3. **Explain trade-offs**: "We chose PostgreSQL over MongoDB because our data is relational..."

4. **Draw diagrams**: Sketch the architecture if asked about data flow

5. **Be honest**: If you don't know, say "I'm not sure, but I would research..."

6. **Show enthusiasm**: Talk about what you learned and challenges overcome

7. **Know the numbers**:
   - 15 minute bidding window
   - 5km initial search radius
   - 10 coins = ₹1 discount
   - 80% quiz score = 10 coins reward

---

## 🔧 Troubleshooting Questions

**Q: What if WebSocket disconnects?**
A: Frontend has reconnection logic with exponential backoff. Falls back to polling if WebSocket fails.

**Q: What if payment fails midway?**
A: Transaction is not committed until Razorpay signature is verified. Booking stays in TUTOR_SELECTED state.

**Q: How do you prevent SQL injection?**
A: SQLAlchemy ORM parameterizes all queries automatically. Never concatenate user input into SQL strings.

**Q: How do you handle CORS errors?**
A: FastAPI middleware allows cross-origin requests from any domain in development. Production would whitelist specific domains.

---

**Good luck with your viva! 🎓🚗**

*Document created: November 29, 2025*
*Project: Uber First Gear - Driving Lesson Marketplace*
