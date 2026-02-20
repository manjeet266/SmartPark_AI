import cv2
import numpy as np
import json
from datetime import datetime

# GLOBAL CACHE for Slot Status
# Format: { lot_id: { slot_id: 'full' | 'available' } }
LOT_STATUS_CACHE = {}

def check_parking_space(img, img_processed, slots, active_bookings, lot_id):
    overlay = img.copy()
    
    current_status = {}
    
    for slot in slots:
        # 1. Parse the Points (stored as JSON string)
        try:
            points = np.array(json.loads(slot.points), np.int32)
            points = points.reshape((-1, 1, 2))
        except:
            continue

        # 2. Create a Mask for this specific polygon
        mask = np.zeros(img_processed.shape, dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        
        # 3. Extract pixels ONLY inside this polygon
        img_masked = cv2.bitwise_and(img_processed, img_processed, mask=mask)
        count = cv2.countNonZero(img_masked)

        # Logic
        is_occupied = count > 800 # Threshold may need adjusting for polygons
        is_booked = slot.id in active_bookings
        
        status_key = 'available'
        if is_occupied:
            color = (0, 0, 255)   # Red
            status = "OCCUPIED"
            status_key = 'full'
        elif is_booked:
            color = (0, 255, 255) # Yellow
            status = "BOOKED"
            status_key = 'reserved'
        else:
            color = (0, 255, 0)   # Green
            status = "FREE"
            
        current_status[slot.id] = status_key

        # 4. Draw Polygon
        cv2.polylines(img, [points], True, color, 2)
        
        # 5. Draw Label (Find center of polygon)
        M = cv2.moments(points)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = points[0][0][0], points[0][0][1]

        cv2.putText(img, slot.slot_label, (cX - 10, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

    # Update Global Cache
    LOT_STATUS_CACHE[lot_id] = current_status
    return img

def generate_frames(parking_lot_id):
    from app import app
    from database.models import db, ParkingLot, Slot, Booking
    
    with app.app_context():
        lot = db.session.get(ParkingLot, parking_lot_id)
        if not lot: return
        
        cap = cv2.VideoCapture(lot.video_path)
        
        while True:
            success, img = cap.read()
            if not success:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
            img_thresh = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY_INV, 25, 16)
            img_median = cv2.medianBlur(img_thresh, 5)
            kernel = np.ones((3, 3), np.uint8)
            img_dilate = cv2.dilate(img_median, kernel, iterations=1)
            
            # Get Slots
            slots = db.session.query(Slot).filter_by(parking_lot_id=parking_lot_id).all()
            
            # Get Bookings
            now = datetime.now()
            active_bookings = db.session.query(Booking).filter(
                Booking.start_time <= now, Booking.end_time >= now, Booking.is_active == True
            ).all()
            active_ids = [b.slot_id for b in active_bookings]

            img_final = check_parking_space(img, img_dilate, slots, active_ids, parking_lot_id)
            
            ret, buffer = cv2.imencode('.jpg', img_final)
            frame = buffer.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')