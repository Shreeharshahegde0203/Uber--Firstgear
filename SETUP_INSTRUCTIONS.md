# 🚀 Setup Instructions for New Users

## Prerequisites
- Python 3.10+
- PostgreSQL database
- Git

---

## 📝 Step-by-Step Setup

### 1. Install PostgreSQL
- Download: https://www.postgresql.org/download/
- During installation, **remember your postgres password!**
- Use default port: 5432

### 2. Create Database
Open pgAdmin or psql and run:
```sql
CREATE DATABASE uberclon;
```

### 3. Clone Repository
```bash
git clone https://github.com/Shreeharshahegde0203/Uber--Firstgear.git
cd Uber--Firstgear/mini-uber
```

### 4. Create `.env` File
Create a file named `.env` in the `mini-uber` folder with YOUR database credentials:

```bash
# ⚠️ IMPORTANT: Change these to YOUR PostgreSQL credentials!
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@localhost/uberclon

# API Configuration (keep as is)
API_KEY=your_secret_key
DEBUG=True
```

**Example:**
If your PostgreSQL password is `mypassword123`, your `.env` should be:
```bash
DATABASE_URL=postgresql://postgres:mypassword123@localhost/uberclon
API_KEY=your_secret_key
DEBUG=True
```

### 5. Install Python Dependencies
```bash
pip install -r requirements.txt
```

If you get errors, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Setup Database Tables
```bash
python setup_database.py
python create_sample_data.py
```

This creates:
- Users table with test drivers and riders
- Rides table
- Payments table

### 7. Start the Server
```bash
cd server
python run.py
```

You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000
✅ Matching Engine started
```

### 8. Launch Clients (Optional)
In a NEW terminal:
```bash
cd mini-uber
python start_multiple_clients.py
```

This opens 4 browser windows automatically.

---

## 🔑 Test User Credentials

**Drivers:**
- Username: `driver4` | Password: `password`
- Username: `driver7` | Password: `password`

**Riders:**
- Username: `rider1` | Password: `password`
- Username: `rider5` | Password: `password`
- Username: `rider6` | Password: `password`

---

## ❌ Common Issues & Solutions

### Issue 1: "ModuleNotFoundError"
**Solution:** Install missing packages
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
```

### Issue 2: "could not connect to server"
**Solution:** Check PostgreSQL is running
- Windows: Open "Services" → Find "postgresql" → Start
- Or restart computer

### Issue 3: "database uberclon does not exist"
**Solution:** Create the database
```sql
psql -U postgres
CREATE DATABASE uberclon;
\q
```

### Issue 4: "password authentication failed"
**Solution:** Fix `.env` file with correct password
```bash
DATABASE_URL=postgresql://postgres:CORRECT_PASSWORD@localhost/uberclon
```

### Issue 5: "Port 8000 already in use"
**Solution:** Kill existing process
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or restart computer
```

### Issue 6: Browser can't connect
**Solution:** 
- Check if server is running (should see "Uvicorn running" in terminal)
- Try http://localhost:8000 instead of http://0.0.0.0:8000
- Disable firewall temporarily

---

## 📂 Project Structure

```
mini-uber/
├── .env                    ← ⚠️ CREATE THIS with YOUR credentials!
├── requirements.txt        ← Python packages list
├── setup_database.py       ← Run first time only
├── create_sample_data.py   ← Creates test users
├── start_multiple_clients.py
│
├── server/
│   ├── run.py             ← Start server here
│   └── app/
│       ├── main.py
│       ├── db/
│       │   ├── database.py  ← Reads .env for database connection
│       │   └── models.py
│       └── api/
│
├── client/
│   ├── driver.html
│   └── index.html
│
└── utils/
    ├── check_system.py     ← Check if system is working
    └── set_drivers_online.py
```

---

## ✅ Verify Installation

Run this to check everything works:
```bash
python utils/check_system.py
```

Should show:
```
✅ Database: Connected
✅ Drivers: 2 online
✅ Riders: 3 total
✅ Rides: 0 pending
```

---

## 🆘 Need Help?

1. Check server terminal for error messages
2. Check PostgreSQL is running
3. Verify `.env` file has correct password
4. Run `python utils/check_system.py` to diagnose

---

## 🔐 Security Note

**DO NOT share your `.env` file or commit it to Git!**

The `.env` file contains sensitive credentials. Each person should have their own `.env` file with their own database password.

---

## 📱 Next Steps After Setup

1. Start server: `cd server && python run.py`
2. Open browser: http://localhost:8000/driver.html
3. Login as driver4 / password
4. Click "Go Online"
5. In another tab: http://localhost:8000/index.html
6. Login as rider6 / password
7. Request a ride
8. Watch the magic happen! 🚖

---

**Good luck! 🎉**
