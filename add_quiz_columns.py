from sqlalchemy import create_engine, text
from server.app.db.database import DATABASE_URL

def add_columns():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            # Add coins column
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0"))
                print("Added 'coins' column.")
            except Exception as e:
                if "already exists" in str(e):
                    print("'coins' column already exists.")
                else:
                    print(f"Error adding 'coins': {e}")

            # Add last_quiz_date column
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_quiz_date TIMESTAMP"))
                print("Added 'last_quiz_date' column.")
            except Exception as e:
                if "already exists" in str(e):
                    print("'last_quiz_date' column already exists.")
                else:
                    print(f"Error adding 'last_quiz_date': {e}")
                
            print("✅ Database schema check complete.")
        except Exception as e:
            print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    add_columns()
