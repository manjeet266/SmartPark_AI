from flask import Flask
from database.models import db, User, Booking
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    try:
        # Find a customer
        customer = User.query.filter_by(role='customer').first()
        if not customer:
            print("No customer found.")
            exit()
            
        print(f"Testing bookings for user {customer.uname} (ID: {customer.id})")
        
        # Test query
        my_bookings = db.session.query(Booking).filter(Booking.user_id == customer.id).order_by(Booking.start_time.desc()).all()
        print(f"Query successful. Found {len(my_bookings)} bookings.")
        
    except Exception as e:
        print(f"Query FAILED: {e}")
