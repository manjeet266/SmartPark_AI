from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'cc_register'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Unique constraint prevents duplicate usernames [cite: 1381, 1382]
    uname = db.Column(db.String(50), unique=True, nullable=False) 
    # Required phone (limited to 10 for validation) and email
    mobile = db.Column(db.String(10), nullable=False) 
    email = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # Role to distinguish between Customer and Provider
    role = db.Column(db.String(20), nullable=False) 
    status = db.Column(db.String(1), default='1') # Set to 1 for active users
    is_verified = db.Column(db.Boolean, default=False) # Admin verification status
    rdate = db.Column(db.String(20), default=datetime.now().strftime("%d-%m-%Y"))

    
class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('cc_register.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False, default='Unknown')
    video_path = db.Column(db.String(200), nullable=False)
    ref_image_path = db.Column(db.String(200), nullable=False)
    hourly_rate = db.Column(db.Float, default=5.0) 
    upi_id = db.Column(db.String(50), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    
    slots = db.relationship('Slot', backref='parking_lot', lazy=True)
    reviews = db.relationship('Review', backref='parking_lot', lazy=True)

    @property
    def avg_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    @property
    def review_count(self):
        return len(self.reviews)

class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    slot_label = db.Column(db.String(10), nullable=False)
    # Stores coordinates as JSON string: "[[x1,y1], [x2,y2], ...]"
    points = db.Column(db.Text, nullable=False) 

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('slot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('cc_register.id'), nullable=True)
    ticket_uuid = db.Column(db.String(36), unique=True, nullable=True)  # Secure Unique ID
    
    customer_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    vehicle_number = db.Column(db.String(20), nullable=True)
    
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Smart Gate Tracking
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    
    amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(db.String(20), default='Paid')
    payment_method = db.Column(db.String(50), default='Cash') 
    
    is_active = db.Column(db.Boolean, default=True)
    
    slot = db.relationship('Slot', backref='bookings')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('cc_register.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reviews')
