import sqlite3

try:
    conn = sqlite3.connect('smartpark.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(booking)")
    columns = cursor.fetchall()
    print("Columns in booking:")
    for col in columns:
        print(col)
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
