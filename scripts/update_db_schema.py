import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'smartpark.db')

def update_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(parking_lot)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'location' not in columns:
            print("Adding 'location' column to parking_lot table...")
            cursor.execute("ALTER TABLE parking_lot ADD COLUMN location TEXT DEFAULT 'Unknown'")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'location' column already exists.")

    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_schema()
