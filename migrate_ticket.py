from flask import Flask
from sqlalchemy import text
from database.models import db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Attempt to add ticket_uuid column if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE booking ADD COLUMN ticket_uuid VARCHAR(36)"))
            conn.commit()
            print("ticket_uuid column added successfully")
    except Exception as e:
        print(f"Migration info (might already exist): {e}")
