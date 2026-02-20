from app import app, db
from sqlalchemy import text

def migrate_db():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check if columns exist (this is a simplified check, usually we'd inspect schema)
                # We'll just try to add them and ignore specific errors or check via raw SQL
                
                # SQLite specific syntax (since this looks like a local flask app, likely SQLite)
                # If it's not SQLite, the syntax might differ slightly (e.g., MySQL ADD COLUMN)
                
                # Check for SQLite
                db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                
                # Try adding latitude
                try:
                    conn.execute(text("ALTER TABLE parking_lot ADD COLUMN latitude FLOAT"))
                    print("Added latitude column.")
                except Exception as e:
                    print(f"Latitude column check/add: {e}")

                # Try adding longitude
                try:
                    conn.execute(text("ALTER TABLE parking_lot ADD COLUMN longitude FLOAT"))
                    print("Added longitude column.")
                except Exception as e:
                    print(f"Longitude column check/add: {e}")
                    
                conn.commit()
                print("Migration attempts finished.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == '__main__':
    migrate_db()
