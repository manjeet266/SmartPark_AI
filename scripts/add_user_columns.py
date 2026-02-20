import sqlite3
import os

DB_PATH = r"D:\Final\SmartPark_Flask\SmartPark_Flask\smartpark.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info('user')")
    cols = [r[1] for r in cur.fetchall()]
    print("Existing columns:", cols)

    if 'email' not in cols:
        try:
            cur.execute("ALTER TABLE user ADD COLUMN email TEXT")
            print('Added column: email')
        except Exception as e:
            print('Failed to add email column:', e)

    if 'phone_number' not in cols:
        try:
            cur.execute("ALTER TABLE user ADD COLUMN phone_number TEXT")
            print('Added column: phone_number')
        except Exception as e:
            print('Failed to add phone_number column:', e)

    conn.commit()
    conn.close()
    print('Migration complete.')

if __name__ == '__main__':
    main()
