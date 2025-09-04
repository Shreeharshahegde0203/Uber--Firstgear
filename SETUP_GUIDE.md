# Mini-Uber Setup Guide

This guide will walk you through3. The `.env` file has been configured with your PostgreSQL connection details:

```
DATABASE_URL=postgresql://postgres:sharsha0203@localhost/uberclon
```

This connects to your PostgreSQL database 'uberclon' using the password 'sharsha0203'.g up and running the mini-Uber application with PostgreSQL.

## Prerequisites

- Python 3.7 or higher
- PostgreSQL server installed and running
- pip package manager

## Step 1: Install PostgreSQL (if not already installed)

### Windows
1. Download the installer from https://www.postgresql.org/download/windows/
2. Run the installer and follow the prompts
3. Remember the password you set for the 'postgres' user
4. Add PostgreSQL bin directory to your PATH environment variable

### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Step 2: Configure PostgreSQL

1. Log in to PostgreSQL:

```bash
# Windows (using psql from the command prompt)
psql -U postgres

# macOS/Linux
sudo -u postgres psql
```

2. The database has already been created:

```sql
-- Database 'uberclon' is already set up
-- If needed to recreate it:
-- CREATE DATABASE uberclon;
```

3. (Optional) Create a dedicated user:

```sql
CREATE USER miniuber_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE miniuber TO miniuber_user;
```

## Step 3: Configure the Application

1. Update the `.env` file with your PostgreSQL connection details:

```
DATABASE_URL=postgresql://postgres:your_password@localhost/miniuber
```

Replace `your_password` with the password for the 'postgres' user (or the dedicated user if you created one).

## Step 4: Set Up the Python Environment

1. Install required Python packages:

```bash
pip install -r requirements.txt
```

## Step 5: Initialize the Database

1. Run the database setup script:

```bash
python setup_database.py
```

2. (Optional) Create sample data:

```bash
python create_sample_data.py
```

## Step 6: Start the Server

```bash
cd server
python run.py
```

The server will start at http://localhost:8000

## Step 7: Start the Client

In a new terminal:

```bash
cd client
python run_client.py
```

The client will be available at http://localhost:3000/index.html

## API Testing

You can test the API using the provided test script:

```bash
cd client
python test_api.py
```

## API Endpoints

- `POST /api/ping` - Test endpoint (sends "ping", receives "pong")
- `GET /api/health` - Health check endpoint
- `GET/POST /api/users` - User management
- `GET/POST /api/rides` - Ride management

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Verify that PostgreSQL is running:
   ```bash
   # Windows
   sc query postgresql
   
   # macOS
   brew services list
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Check your connection string in the `.env` file.

3. Make sure the database exists:
   ```bash
   psql -U postgres -c "\l"
   ```

4. Ensure your PostgreSQL user has proper permissions.

### Package Installation Issues

If you encounter errors installing packages:

1. Update pip:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Install packages one by one to identify problematic packages:
   ```bash
   pip install fastapi
   pip install uvicorn
   # etc.
   ```

### Server Won't Start

1. Check for port conflicts:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # macOS/Linux
   netstat -tuln | grep 8000
   ```

2. Kill any process using port 8000 and try again.

### Client Issues

1. Make sure the server is running before starting the client.
2. Check browser console for JavaScript errors.
3. Verify that your browser allows local file access (for development).
