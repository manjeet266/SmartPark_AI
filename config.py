import os

class Config:
    # 1. Base Directory: Ensures we know exactly where the project folder is
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # 2. Security Key
    SECRET_KEY = 'super_secret_key_for_session'

    # 3. Database Configuration
    # Uses 'os.path.join' to force the DB to be created inside the project folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'smartpark.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 4. File Upload Paths
    # Ensure these folders exist inside 'static/uploads/'
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    UPLOAD_REF_IMAGES = os.path.join(UPLOAD_FOLDER, 'parking_refs')
    UPLOAD_VIDEOS = os.path.join(UPLOAD_FOLDER, 'parking_videos')

    # Max upload size (100MB)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    # 5. PAYMENT & SMS KEYS (Razorpay & Twilio)
    # Replace these with your REAL keys from their websites
    
    # Razorpay (Payment Gateway)
    RAZORPAY_KEY_ID = "rzp_test_YOUR_KEY_HERE"       # Paste Key ID here
    RAZORPAY_KEY_SECRET = "YOUR_SECRET_HERE"         # Paste Key Secret here

    # Twilio (SMS Service) - Optional if you don't need SMS immediately
    TWILIO_SID = "AC_YOUR_ACCOUNT_SID"               # Paste SID here
    TWILIO_AUTH_TOKEN = "YOUR_AUTH_TOKEN"            # Paste Auth Token here
    TWILIO_PHONE_NUMBER = "+1234567890"              # Paste Twilio Phone Number here