import sys
import importlib.util

def check_module(module_name):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ Module '{module_name}' is installed and working.")
        return True
    except ImportError as e:
        print(f"❌ Module '{module_name}' cannot be imported: {e}")
        return False

def check_postgres_connection():
    """Check connection to PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://postgres:sharsha0203@localhost/uberclon")
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print("✅ Successfully connected to PostgreSQL!")
        print(f"   PostgreSQL version: {version[0]}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema='public'
        """)
        tables = cursor.fetchall()
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n=== Testing Mini-Uber System Components ===\n")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check required modules
    modules_to_check = [
        "fastapi", "uvicorn", "sqlalchemy", "psycopg2", "pydantic", 
        "dotenv", "requests", "bcrypt"
    ]
    
    modules_ok = True
    for module in modules_to_check:
        if not check_module(module):
            modules_ok = False
    
    # Only check database if modules are OK
    if modules_ok:
        db_ok = check_postgres_connection()
    else:
        db_ok = False
    
    # Print summary
    print("\n=== Test Summary ===")
    if modules_ok:
        print("✅ All required modules are installed.")
    else:
        print("❌ Some required modules are missing.")
    
    if db_ok:
        print("✅ PostgreSQL connection successful.")
    else:
        print("❌ PostgreSQL connection failed.")
    
    if modules_ok and db_ok:
        print("\n✅ System is ready to run!")
        print("To run the server: cd server && python run.py")
        print("To run the client: cd client && python run_client.py")
    else:
        print("\n❌ System setup is incomplete. Please fix the issues above.")

if __name__ == "__main__":
    main()
