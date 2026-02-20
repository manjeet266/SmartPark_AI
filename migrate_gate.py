from flask import Flask
from sqlalchemy import text
from database.models import db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Attempt to add columns if they don't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE booking ADD COLUMN check_in_time DATETIME"))
            conn.execute(text("ALTER TABLE booking ADD COLUMN check_out_time DATETIME"))
            conn.commit()
            print("Columns added successfully")
    except Exception as e:
        print(f"Migration info (might already exist): {e}")
