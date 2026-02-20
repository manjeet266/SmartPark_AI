
import sqlite3
import os

DB_PATH = "smartpark.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Check table info for 'cc_register' (from User model) or 'user' (if db_setup used default)
        try:
            print("--- Table Info: cc_register ---")
            cur.execute("PRAGMA table_info(cc_register)")
            cols = cur.fetchall()
            for col in cols:
                print(col)
        except Exception as e:
            print(f"Error checking cc_register: {e}")

        # Check existing users
        print("\n--- Users in cc_register ---")
        try:
            cur.execute("SELECT * FROM cc_register")
            users = cur.fetchall()
            for user in users:
                print(user)
        except Exception as e:
            print(f"Error querying cc_register: {e}")

        conn.close()
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    main()
