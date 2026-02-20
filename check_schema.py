import sqlite3

try:
    conn = sqlite3.connect('smartpark.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(cc_register)")
    columns = cursor.fetchall()
    print("Columns in cc_register:")
    for col in columns:
        print(col)
        
    print("-" * 20)
    
    cursor.execute("PRAGMA table_info(parking_lot)")
    columns = cursor.fetchall()
    print("Columns in parking_lot:")
    for col in columns:
        print(col)

    conn.close()
except Exception as e:
    print(f"Error: {e}")
