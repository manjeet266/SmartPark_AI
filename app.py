import cv2
import numpy as np
from flask import Flask
import os
import json

import qrcode
import io
import base64
from twilio.rest import Client
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, Response, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from sqlalchemy import func

# 1. Setup App & Config
from config import Config
from database.models import db, User, ParkingLot, Slot, Booking, Review

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Initialize Database
db.init_app(app)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

# --- SMS HELPER FUNCTION ---
def send_confirmation_sms(to_number, customer_name, slot_label, amount):
    try:
        # Only attempt if keys are set (prevents crash if you don't have keys yet)
        if "YOUR_" in app.config['TWILIO_SID']: 
            print(f"⚠️ Mock SMS to {to_number}: Booking Confirmed for {slot_label}. Paid ₹{amount}")
            return

        client = Client(app.config['TWILIO_SID'], app.config['TWILIO_AUTH_TOKEN'])
        message = client.messages.create(
            body=f"✅ SmartPark Confirmed!\nHi {customer_name}, your parking slot {slot_label} is booked.\nPaid: ₹{amount}\nThank you!",
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=to_number
        )
        print(f"SMS Sent: {message.sid}")
    except Exception as e:
        print(f"⚠️ SMS Failed: {e}")

# 2. Import Detector
try:
    from core.detector import generate_frames
except ImportError:
    print("⚠️ Warning: core.detector not found.")

def allowed_file(filename, file_type):
    if file_type == 'image':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}
    elif file_type == 'video':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}
    return False

# --- ROUTES: GENERAL ---
@app.route('/')
def landing_page(): return render_template('landing.html')

@app.route('/home')
def home():
    lots = db.session.query(ParkingLot).all()
    return render_template('home.html', lots=lots)

@app.route('/terms')
def terms_page():
    return render_template('legal/terms.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('landing_page'))

# --- ROUTES: AUTH ---
@app.route('/login/provider', methods=['GET', 'POST'])
def login_provider():
    if request.method == 'POST':
        user = db.session.query(User).filter_by(uname=request.form['username'], role='provider').first()
        if user and user.password == request.form['password']:
            session['user_id'] = user.id
            session['role'] = 'provider'
            flash(f'Welcome {user.uname}!')
            return redirect(url_for('provider_dashboard'))
        flash('Invalid credentials.')
    return render_template('auth/login_provider.html')

@app.route('/login/customer', methods=['GET', 'POST'])
def login_customer():
    if request.method == 'POST':
        user = db.session.query(User).filter_by(uname=request.form['username'], role='customer').first()
        if user and user.password == request.form['password']:
            session['user_id'] = user.id
            session['role'] = 'customer'
            flash(f'Welcome {user.uname}!')
            return redirect(url_for('customer_dashboard'))
        flash('Invalid credentials.')
    return render_template('auth/login_customer.html')

@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        # Hardcoded Admin Credentials for Demo
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 0
            session['role'] = 'admin'
            flash('Admin Logged in.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid Admin Credentials.', 'danger')
    return render_template('auth/login_admin.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    
    # Fetch data
    pending_providers = db.session.query(User).filter_by(role='provider', is_verified=False).all()
    all_providers = db.session.query(User).filter_by(role='provider').all()
    all_customers = db.session.query(User).filter_by(role='customer').all()
    all_bookings = db.session.query(Booking).order_by(Booking.start_time.desc()).limit(50).all() # Show last 50
    
    # Stats
    total_income = db.session.query(func.sum(Booking.amount)).scalar() or 0.0
    stats = {
        'providers': len(all_providers),
        'customers': len(all_customers),
        'pending': len(pending_providers),
        'revenue': round(total_income, 2)
    }

    return render_template('admin/dashboard.html', 
                           pending=pending_providers, 
                           all_providers=all_providers, 
                           customers=all_customers, 
                           bookings=all_bookings,
                           stats=stats)

@app.route('/admin/verify_provider/<int:id>')
def verify_provider(id):
    if session.get('role') != 'admin': return redirect(url_for('login_admin'))
    
    provider = db.session.query(User).get(id)
    if provider:
        provider.is_verified = True
        db.session.commit()
        flash(f'Provider {provider.uname} Verified!', 'success')
    return redirect(url_for('admin_dashboard'))
    
# Registration Route with Unique Username and Password Verification
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form.get('uname')
        password = request.form.get('pass')
        confirm_pass = request.form.get('confirm_pass')
        mobile = request.form.get('mobile')
        role = request.form.get('role')
        
        # 1. Check if Username is Unique
        existing_user = User.query.filter_by(uname=uname).first()
        if existing_user:
            flash('This username is already taken. Please choose another.', 'danger')
            return redirect(url_for('register'))

        # 2. Verify Password Confirmation
        if password != confirm_pass:
            flash('Passwords do not match!', 'warning')
            return redirect(url_for('register'))

        # 3. Create and Save New User
        try:
            # New Providers are NOT Verified by default
            is_verified = True if role == 'customer' else False

            new_user = User(
                name=request.form.get('name'),
                uname=uname,
                mobile=mobile,
                email=request.form.get('email'),
                location=request.form.get('location'),
                password=password,
                role=role,
                is_verified=is_verified 
            )
            db.session.add(new_user)
            db.session.commit()
            
            if role == 'provider':
                flash('Account created! Please wait for Admin Verification.', 'info')
                return redirect(url_for('login_provider'))
            else:
                flash('Account created successfully!', 'success')
                return redirect(url_for('login_customer'))
                
        except Exception as e:
            db.session.rollback()
            print(f"Registration Error: {e}")
            flash('Registration failed. Please try again.', 'danger')

    return render_template('auth/register.html')


# --- ROUTES: PROVIDER ---
# --- ROUTES: PROVIDER ---
@app.route('/provider/dashboard')
def provider_dashboard():
    if 'user_id' not in session or session.get('role') != 'provider': return redirect(url_for('login_provider'))
    provider_id = session['user_id']
    
    provider = db.session.query(User).get(provider_id)
    # Warning for Unverified Providers
    if not provider.is_verified:
        flash("⚠️ Your account is NOT verified yet. Your parking lots are hidden from customers.", "warning")

    my_lots = db.session.query(ParkingLot).filter_by(provider_id=provider_id).all()
    total_income = db.session.query(func.sum(Booking.amount)).join(Slot).join(ParkingLot).filter(ParkingLot.provider_id == provider_id).scalar() or 0.0
    today = date.today()
    daily_income = db.session.query(func.sum(Booking.amount)).join(Slot).join(ParkingLot).filter(ParkingLot.provider_id == provider_id).filter(func.date(Booking.start_time) == today).scalar() or 0.0
    bookings = db.session.query(Booking).join(Slot).join(ParkingLot).filter(ParkingLot.provider_id == provider_id).order_by(Booking.start_time.desc()).all()
    
    # Fetch Reviews for all lots owned by this provider
    reviews = db.session.query(Review).join(ParkingLot).filter(ParkingLot.provider_id == provider_id).order_by(Review.created_at.desc()).all()

    return render_template('provider/dashboard.html', lots=my_lots, bookings=bookings, total_income=round(total_income, 2), daily_income=round(daily_income, 2), reviews=reviews, is_verified=provider.is_verified)

@app.route('/provider/create_lot', methods=['GET', 'POST'])
def create_lot():
    if 'user_id' not in session: return redirect(url_for('login_provider'))
    if request.method == 'POST':
        name = request.form['name']
        rate = float(request.form.get('hourly_rate', 5.0))
        ref_image = request.files['ref_image']
        video_file = request.files['video_file']
        if ref_image and video_file:
            ref_filename = secure_filename(ref_image.filename)
            vid_filename = secure_filename(video_file.filename)
            ref_path = os.path.join(app.config['UPLOAD_REF_IMAGES'], ref_filename)
            vid_path = os.path.join(app.config['UPLOAD_VIDEOS'], vid_filename)
            ref_image.save(ref_path)
            video_file.save(vid_path)
            location = request.form.get('location', 'Unknown')
            upi_id = request.form.get('upi_id')
            
            # Helper to safe convert
            def to_float(val):
                try: return float(val) if val else None
                except: return None
                
            latitude = to_float(request.form.get('latitude'))
            longitude = to_float(request.form.get('longitude'))
            
            new_lot = ParkingLot(
                provider_id=session['user_id'], 
                name=name, 
                location=location, 
                upi_id=upi_id, 
                hourly_rate=rate, 
                ref_image_path=f"uploads/parking_refs/{ref_filename}", 
                video_path=vid_path,
                latitude=latitude,
                longitude=longitude
            )
            db.session.add(new_lot)
            db.session.commit()
            return redirect(url_for('setup_slots', lot_id=new_lot.id))
    return render_template('provider/create_lot.html')

@app.route('/provider/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    if 'user_id' not in session: return redirect(url_for('login_provider'))
    lot = db.session.get(ParkingLot, lot_id)
    if not lot or lot.provider_id != session['user_id']: return redirect(url_for('provider_dashboard'))
    if request.method == 'POST':
        lot.name = request.form['name']
        lot.location = request.form['location']
        lot.upi_id = request.form['upi_id']
        lot.hourly_rate = float(request.form['hourly_rate'])
        
        # Helper to safe convert
        def to_float(val):
            try: return float(val) if val else None
            except: return None
            
        lot.latitude = to_float(request.form.get('latitude'))
        lot.longitude = to_float(request.form.get('longitude'))
        
        db.session.commit()
        flash('Updated Successfully!')
        return redirect(url_for('provider_dashboard'))
    return render_template('provider/edit_lot.html', lot=lot)

@app.route('/provider/setup/<int:lot_id>')
def setup_slots(lot_id):
    lot = db.session.get(ParkingLot, lot_id)
    if not lot: return "Not found", 404
    return render_template('provider/setup_slots.html', lot=lot)

@app.route('/api/save_slots', methods=['POST'])
def save_slots():
    data = request.json
    lot_id = data.get('lot_id')
    shapes = data.get('rects') 
    db.session.query(Slot).filter_by(parking_lot_id=lot_id).delete()
    for i, points in enumerate(shapes):
        points_json = json.dumps(points)
        new_slot = Slot(parking_lot_id=lot_id, slot_label=f"Slot-{i+1}", points=points_json)
        db.session.add(new_slot)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/provider/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    if 'user_id' not in session: return redirect(url_for('login_provider'))
    lot = db.session.get(ParkingLot, lot_id)
    if lot and lot.provider_id == session.get('user_id'):
        slots = db.session.query(Slot).filter_by(parking_lot_id=lot_id).all()
        for slot in slots:
            db.session.query(Booking).filter_by(slot_id=slot.id).delete()
        db.session.query(Slot).filter_by(parking_lot_id=lot_id).delete()
        db.session.delete(lot)
        db.session.commit()
        flash('Lot Deleted.')
    return redirect(url_for('provider_dashboard'))

# --- ROUTES: CUSTOMER ---
@app.route('/customer/dashboard')
def customer_dashboard():
    if 'user_id' not in session or session.get('role') != 'customer': return redirect(url_for('login_customer'))
    
    q = request.args.get('q', '').strip()
    
    # FILTER: Only show lots from VERIFIED providers
    if q:
        search = f"%{q}%"
        all_lots = db.session.query(ParkingLot).join(User).filter(
            User.is_verified == True,
            (ParkingLot.name.ilike(search)) | (ParkingLot.location.ilike(search))
        ).all()
    else:
        all_lots = db.session.query(ParkingLot).join(User).filter(User.is_verified == True).all()
        
    my_bookings = db.session.query(Booking).filter(Booking.user_id == session['user_id']).order_by(Booking.start_time.desc()).all()
    return render_template('customer/dashboard.html', lots=all_lots, bookings=my_bookings, now=datetime.now())

@app.route('/customer/live/<int:lot_id>')
def view_lot(lot_id):
    lot = db.session.get(ParkingLot, lot_id)
    if not lot: return "Lot not found", 404
    slots = db.session.query(Slot).filter_by(parking_lot_id=lot_id).all()
    
    # Calculate Slot Status
    now = datetime.now()
    slot_status = {slot.id: 'available' for slot in slots}
    
    bookings = db.session.query(Booking).join(Slot).filter(Slot.parking_lot_id == lot_id, Booking.is_active == True).all()
    
    for b in bookings:
        if b.start_time <= now <= b.end_time:
            slot_status[b.slot_id] = 'full' # Red (Occupied/Active)
        elif b.start_time > now and b.start_time.date() == now.date():
            # Only mark as reserved if currently available (don't overwrite 'full')
            if slot_status[b.slot_id] == 'available':
                slot_status[b.slot_id] = 'reserved' # Yellow (Future today)

    # Fetch Reviews
    reviews = db.session.query(Review).filter_by(parking_lot_id=lot_id).order_by(Review.created_at.desc()).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
        
    return render_template('customer/view_lot.html', lot=lot, slots=slots, slot_status=slot_status, rzp_key=app.config['RAZORPAY_KEY_ID'], reviews=reviews, avg_rating=round(avg_rating, 1))

@app.route('/video_feed/<int:lot_id>')
def video_feed(lot_id):
    return Response(generate_frames(lot_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/live_status/<int:lot_id>')
def features_live_status(lot_id):
    # Retrieve status from the shared GLOBAL CACHE in detector.py
    # This ensures exact synchronization with the video feed being generated.
    try:
        from core.detector import LOT_STATUS_CACHE
        if lot_id in LOT_STATUS_CACHE:
             return jsonify(LOT_STATUS_CACHE[lot_id])
        else:
             # Fallback if video hasn't started or cache empty
             return jsonify({})
    except ImportError:
         return jsonify({})

# --- REVIEWS & RATING ---
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'user_id' not in session: return redirect(url_for('login_customer'))
    
    lot_id = request.form.get('lot_id')
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    
    if not lot_id or not rating:
        flash("Invalid review data", "error")
        return redirect(url_for('customer_dashboard'))

    new_review = Review(
        parking_lot_id=lot_id,
        user_id=session['user_id'],
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()
    flash('Review Submitted!', 'success')
    return redirect(url_for('customer_dashboard'))

# --- QR CODE TICKET ---
@app.route('/get_qr/<int:booking_id>')
def get_qr(booking_id):
    if 'user_id' not in session: return "Unauthorized", 403
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != session.get('user_id'):
        return "Unauthorized", 403
    
    # Data to encode
    display_id = booking.ticket_uuid if booking.ticket_uuid else f"#{booking.id}"
    # Handle missing slot/lot (e.g. if lot was re-configured)
    if booking.slot and booking.slot.parking_lot:
        lot_name = booking.slot.parking_lot.name
        slot_label = booking.slot.slot_label
    else:
        lot_name = "Unknown Lot (Deleted)"
        slot_label = "N/A"

    data = f"SMARTPARK TICKET\nBooking ID: {display_id}\nLot: {lot_name}\nSlot: {slot_label}\nVehicle: {booking.vehicle_number}\nStart: {booking.start_time}\nEnd: {booking.end_time}\nStatus: {booking.payment_status}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return Response(img_io, mimetype='image/png')

# --- NEW: RAZORPAY CREATE ORDER ---
@app.route('/create_payment_order', methods=['POST'])
def create_payment_order():
    if 'user_id' not in session: return jsonify({"status": "error", "message": "Login required"})
    
    amount = float(request.json.get('amount'))
    # Razorpay expects amount in PAISE (multiply by 100)
    amount_paise = int(amount * 100)
    
    # Mock Payment Order if keys are not set
    if "YOUR_KEY" in app.config['RAZORPAY_KEY_ID']:
        return jsonify({
            "status": "success", 
            "order_id": f"order_mock_{int(datetime.now().timestamp())}", 
            "amount": amount_paise
        })

    try:
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"receipt_order_{datetime.now().timestamp()}",
            "payment_capture": 1 # Auto capture
        }
        order = razorpay_client.order.create(data=order_data)
        return jsonify({"status": "success", "order_id": order['id'], "amount": amount_paise})
    except Exception as e:
        print(f"Razorpay Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/book_slot_confirm', methods=['POST'])
def book_slot_confirm():
    if 'user_id' not in session: return jsonify({"status": "error", "message": "Login required"})
    
    data = request.json
    slot_id = data.get('slot_id')
    start_str = data.get('start_time')
    duration = int(data.get('duration'))
    
    # 1. Parse Time
    try: start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
    except: start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%S')
    end_time = start_time + timedelta(hours=duration)
    
    # 2. Conflict Check
    conflict = db.session.query(Booking).filter(
        Booking.slot_id == slot_id, Booking.is_active == True,
        Booking.start_time < end_time, Booking.end_time > start_time
    ).first()
    if conflict: return jsonify({"status": "error", "message": "Slot already booked!"})

    # 3. Create Booking
    slot = db.session.get(Slot, slot_id)
    total_cost = slot.parking_lot.hourly_rate * duration
    
    # Generate Secure Unique Ticket ID
    import uuid
    secure_ticket_id = str(uuid.uuid4())[:5].upper()
    
    new_booking = Booking(
        slot_id=slot_id, user_id=session['user_id'],
        ticket_uuid=secure_ticket_id,
        customer_name=data.get('name'),
        phone_number=data.get('phone'),
        vehicle_number=data.get('vehicle'),
        start_time=start_time, end_time=end_time,
        amount=total_cost, 
        payment_status='Paid',
        payment_method='Razorpay Online'
    )
    db.session.add(new_booking)
    db.session.commit()

    # 4. SEND SMS & WHATSAPP
    # send_confirmation_sms(data.get('phone'), data.get('name'), slot.slot_label, total_cost)
    send_whatsapp_ticket(data.get('phone'), data.get('name'), slot.slot_label, total_cost, start_time, end_time, new_booking.id)

    return jsonify({
        "status": "success", 
        "message": "Booking Confirmed! Details sent to WhatsApp.", 
        "booking_id": new_booking.id,
        "ticket_uuid": new_booking.ticket_uuid 
    })

# --- HELPER: WHATSAPP ---
def send_whatsapp_ticket(to_number, customer_name, slot_label, amount, start, end, booking_id):
    try:
        # Construct body
        msg_body = f"🅿️ *SmartPark Ticket*\n\nHi *{customer_name}*,\nYour booking is confirmed! ✅\n\n🆔 *Booking ID:* #{booking_id}\n📍 *Slot:* {slot_label}\n💰 *Amount:* ₹{amount}\n📅 *Start:* {start}\n🔚 *End:* {end}\n\n📍 *Locate Slot:* https://maps.google.com/?q=parking\n\nShow this message at the gate."
        
        # Ensure number has country code (Assuming +91 for India if missing)
        formatted_num = f"whatsapp:{to_number}" if to_number.startswith('+') else f"whatsapp:+91{to_number}"
        
        # Check if keys are mock
        if "YOUR_" in app.config['TWILIO_SID']: 
            print(f"⚠️ Mock WhatsApp to {formatted_num}:\n{msg_body}")
            return

        client = Client(app.config['TWILIO_SID'], app.config['TWILIO_AUTH_TOKEN'])
        message = client.messages.create(
            body=msg_body,
            from_=f"whatsapp:{app.config['TWILIO_PHONE_NUMBER']}",
            to=formatted_num
        )
        print(f"WhatsApp Sent: {message.sid}")
    except Exception as e:
        print(f"⚠️ WhatsApp Failed: {e}")

# --- BACKGROUND TASK: EXPIRY ALERTS ---
import threading
import time

def check_expiry_alerts():
    with app.app_context():
        # Find active bookings expiring in ~15 mins
        now = datetime.now()
        target = now + timedelta(minutes=15)
        # Check window of 1 minute
        bookings = db.session.query(Booking).filter(
            Booking.payment_status == 'Paid',
            Booking.end_time >= target - timedelta(seconds=30),
            Booking.end_time <= target + timedelta(seconds=30)
        ).all()
        
        for b in bookings:
            print(f"⏰ ALERT: Booking #{b.id} for {b.customer_name} expires in 15 mins!")
            # Send Warning WhatsApp/SMS
            try:
                if "YOUR_" in app.config['TWILIO_SID']: continue
                
                client = Client(app.config['TWILIO_SID'], app.config['TWILIO_AUTH_TOKEN'])
                formatted_num = f"whatsapp:{b.phone_number}" if b.phone_number.startswith('+') else f"whatsapp:+91{b.phone_number}"
                
                client.messages.create(
                    body=f"⏳ *Time Expiring Soon!*\n\nHi {b.customer_name}, your parking session for *{b.slot.slot_label}* expires in 15 minutes.\nPlease extend or vacate the slot to avoid penalties.",
                    from_=f"whatsapp:{app.config['TWILIO_PHONE_NUMBER']}",
                    to=formatted_num
                )
            except Exception as e:
                print(f"Failed to send alert: {e}")

def start_background_worker():
    def run_schedule():
        while True:
            try:
                check_expiry_alerts()
            except Exception as e:
                print(f"Worker Error: {e}")
            time.sleep(60) # Run every minute

    thread = threading.Thread(target=run_schedule)
    thread.daemon = True
    thread.start()

start_background_worker()

@app.route('/admin/get_user/<int:user_id>')
def get_user_details(user_id):
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    user = db.session.get(User, user_id)
    if not user: return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'uname': user.uname,
        'email': user.email,
        'mobile': user.mobile,
        'location': user.location,
        'role': user.role
    })

@app.route('/admin/update_user', methods=['POST'])
def update_user_details():
    if session.get('role') != 'admin': return redirect(url_for('login_admin'))
    
    user_id = request.form.get('user_id')
    user = db.session.get(User, user_id)
    if user:
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.mobile = request.form.get('mobile')
        user.location = request.form.get('location')
        db.session.commit()
        flash(f"User {user.name} updated successfully!", 'success')
    else:
        flash("User not found.", 'danger')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session: return redirect(url_for('login_admin'))
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete:
        if user_to_delete.role == 'provider':
            lots = db.session.query(ParkingLot).filter_by(provider_id=user_id).all()
            for lot in lots:
                slots = db.session.query(Slot).filter_by(parking_lot_id=lot.id).all()
                for slot in slots:
                    db.session.query(Booking).filter_by(slot_id=slot.id).delete()
                db.session.query(Slot).filter_by(parking_lot_id=lot.id).delete()
                db.session.delete(lot)
        elif user_to_delete.role == 'customer':
            db.session.query(Booking).filter_by(user_id=user_id).delete()
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/download_invoice/<int:booking_id>')
def download_invoice(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login_customer'))
    
    booking = Booking.query.get_or_404(booking_id)
    # Ensure usage of correct user rights logic if needed, currently open for demo
    
    # Get provider details (Handle missing slot case)
    if booking.slot and booking.slot.parking_lot:
        provider_id = booking.slot.parking_lot.provider_id
        provider = db.session.query(User).get(provider_id)
    else:
        provider = None # Handle in template
    user = db.session.query(User).get(session['user_id'])
    
    return render_template('customer/invoice.html', booking=booking, provider=provider, user=user)

# --- SMART GATE / BOOM BARRIER API ---
@app.route('/provider/gate_scanner/<int:lot_id>')
def gate_scanner_page(lot_id):
    if 'user_id' not in session or session.get('role') != 'provider': return redirect(url_for('login_provider'))
    lot = db.session.get(ParkingLot, lot_id)
    return render_template('provider/gate_scanner.html', lot=lot)

@app.route('/api/scan_gate', methods=['POST'])
def scan_gate_api():
    try:
        data = request.json
        booking_id = data.get('booking_id')
        lot_id = int(data.get('lot_id'))
        
        # Robust Lookup Logic
        booking = None
        
        # 1. Search by Ticket UUID (Exact Match) - Works for Long, Short, and Numeric-looking UUIDs
        booking = db.session.query(Booking).filter_by(ticket_uuid=booking_id).first()
        
        # 2. If not found, and input looks like a simple ID (digits), try Primary Key
        if not booking and str(booking_id).isdigit():
             booking = db.session.get(Booking, int(booking_id))
             
        # 3. Handle "#123" format checks
        if not booking and str(booking_id).startswith('#'):
             clean_id = str(booking_id).replace('#', '')
             if clean_id.isdigit():
                 booking = db.session.get(Booking, int(clean_id))
        
        # Validation 1: Booking Exists
        if not booking:
            return jsonify({'status': 'error', 'message': '❌ Invalid Ticket ID'})
            
        # Validation 2: Correct Lot
        if not booking.slot:
             return jsonify({'status': 'error', 'message': '❌ Invalid Booking (Slot Deleted)'})

        if booking.slot.parking_lot_id != lot_id:
             return jsonify({'status': 'error', 'message': '⛔ Wrong Parking Lot!'})
            
        # Validation 3: Time Valid (Roughly)
        now = datetime.now()
        # Allow entry 15 mins before start
        if now < booking.start_time - timedelta(minutes=15):
             return jsonify({'status': 'error', 'message': f'⏳ Too Early! Starts at {booking.start_time.strftime("%H:%M")}'})
        
        # Logic: Entry or Exit?
        if not booking.check_in_time:
            # --- CHECK IN ---
            booking.check_in_time = now
            db.session.commit()
            return jsonify({
                'status': 'success', 
                'mode': 'entry', 
                'message': f'✅ Welcome {booking.customer_name}!',
                'slot': booking.slot.slot_label,
                'vehicle': booking.vehicle_number
            })
            
        elif not booking.check_out_time:
            # --- CHECK OUT ---
            booking.check_out_time = now
            booking.is_active = False # Mark session done
            
            # Check Overstay
            overstay_msg = ""
            if now > booking.end_time:
                overdue = now - booking.end_time
                minutes = int(overdue.total_seconds() / 60)
                overstay_msg = f"⚠️ Overstayed by {minutes} mins."
                
            db.session.commit()
            return jsonify({
                'status': 'success', 
                'mode': 'exit', 
                'message': f'👋 Goodbye! {overstay_msg}',
                'slot': booking.slot.slot_label
            })
            
        else:
             return jsonify({'status': 'error', 'message': '⛔ Ticket Already Used (Out)'})

    except Exception as e:
        print(f"Gate Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/provider/download_log/<int:lot_id>')
def download_log(lot_id):
    if 'user_id' not in session or session.get('role') != 'provider': return redirect(url_for('login_provider'))
    
    lot = db.session.get(ParkingLot, lot_id)
    if not lot: return "Not Found", 404
    
    # Fetch all bookings for this lot, ordered by start time
    bookings = db.session.query(Booking).join(Slot).filter(Slot.parking_lot_id == lot_id).order_by(Booking.start_time.desc()).all()
    
    # Render a printer-friendly template
    return render_template('provider/log_report.html', lot=lot, bookings=bookings, now=datetime.now())

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
