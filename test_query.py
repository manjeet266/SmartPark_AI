from flask import Flask
from database.models import db, User, ParkingLot
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    try:
        print("Testing query...")
        all_lots = db.session.query(ParkingLot).join(User).filter(User.is_verified == True).all()
        print(f"Query successful. Found {len(all_lots)} lots.")
    except Exception as e:
        print(f"Query FAILED: {e}")
