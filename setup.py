import os
import sys
import subprocess
import platform

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def run_command(command, description=None):
    """Run a shell command and print its output"""
    if description:
        print(f"\n> {description}")
    
    print(f"$ {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f"Error: {result.stderr}")
    
    return result.returncode == 0

def check_python():
    """Check if Python is installed with the correct version"""
    print_header("Checking Python installation")
    
    try:
        version = subprocess.check_output(["python", "--version"], text=True)
        print(f"Found {version.strip()}")
        return True
    except:
        try:
            version = subprocess.check_output(["python3", "--version"], text=True)
            print(f"Found {version.strip()}")
            return True
        except:
            print("Error: Python not found. Please install Python 3.7 or higher.")
            return False

def check_postgres():
    """Check if PostgreSQL is installed"""
    print_header("Checking PostgreSQL installation")
    
    if platform.system() == "Windows":
        # On Windows, check if psql is in PATH
        result = subprocess.run(["where", "psql"], shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("PostgreSQL is installed.")
            return True
    else:
        # On Linux/Mac, use which
        result = subprocess.run(["which", "psql"], shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("PostgreSQL is installed.")
            return True
    
    print("Warning: PostgreSQL executable not found in PATH.")
    print("If PostgreSQL is already installed, make sure it's in your PATH.")
    print("Otherwise, please install PostgreSQL from https://www.postgresql.org/download/")
    
    answer = input("Continue anyway? (y/n): ")
    return answer.lower() == 'y'

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing dependencies")
    return run_command("pip install -r requirements.txt", "Installing Python packages")

def setup_database():
    """Set up the PostgreSQL database"""
    print_header("Setting up database")
    return run_command("python setup_database.py", "Creating and initializing database")

def main():
    print_header("Mini-Uber Setup")
    
    # Check requirements
    if not check_python():
        return False
    
    if not check_postgres():
        print("\nWarning: Proceeding without confirmed PostgreSQL installation.")
    
    # Check .env file
    if not os.path.exists(".env"):
        print("\nWarning: .env file not found. Using default configuration.")
    
    # Install dependencies
    if not install_dependencies():
        print("Error installing dependencies. Please fix the errors and try again.")
        return False
    
    # Set up database
    if not setup_database():
        print("Error setting up database. Please fix the errors and try again.")
        return False
    
    print_header("Setup Complete!")
    print("""
Next steps:
1. Start the server:
   $ cd server
   $ python run.py

2. Start the client:
   $ cd client
   $ python run_client.py

3. Test the API:
   $ cd client
   $ python test_api.py
""")
    
    return True

if __name__ == "__main__":
    if not main():
        sys.exit(1)
