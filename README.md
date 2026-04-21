<div align="center">
  <img src="https://images.unsplash.com/photo-1573348722427-f1d6819fdf98?q=80&w=1200&auto=format&fit=crop" alt="Smart Parking System" width="100%" style="border-radius:15px; margin-bottom: 20px;">

  # 🅿️ SmartPark Flask
  **An Advanced Computer Vision-Powered Smart Parking Management System**

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" />
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
    <img src="https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=Twilio&logoColor=white" />
    <img src="https://img.shields.io/badge/Computer%20Vision-FF6F00?style=for-the-badge&logo=opencv&logoColor=white" />
  </p>

  [Features](#features) •
  [Tech Stack](#tech-stack) •
  [Installation](#installation) •
  [Configuration](#configuration) •
  [Usage](#usage)
</div>

---

## 📖 Overview

**SmartPark Flask** is a comprehensive, multi-role web application designed to digitize and automate parking lot management. Built with Flask, it leverages **Computer Vision** for live slot availability tracking, **Twilio** for WhatsApp/SMS integration, and **Razorpay** for seamless online payments. 

Whether you are an administrator, a parking lot provider, or a customer looking for a spot, SmartPark offers a tailored, seamless experience.

---

## ✨ Features

### 👤 Customer Features
- **Discover & Secure:** Find nearby verified parking lots with live availability.
- **Smart Booking:** Book slots seamlessly and receive digital QR-code tickets.
- **WhatsApp/SMS Alerts:** Get instant booking confirmations and expiry alerts (15 mins prior) via Twilio.
- **Reviews & Ratings:** Review your parking experience to help others.
- **Razorpay Integration:** Pay securely online.

### 🏢 Provider Features
- **Lot Management:** Register, manage, and price your parking lots.
- **Visual Slot Mapping:** Define layout geometries for individual parking slots to integrate with camera feeds.
- **Smart Gate Scanner:** Use the built-in gate scanner API to check in/out customers via their QR tickets.
- **Live Feed & CV:** Connect camera feeds to automatically track which slots are occupied or available.
- **Analytics & Logs:** Track revenue, daily income, and download comprehensive logs.

### 🛠️ Admin Features
- **Centralized Dashboard:** View holistic system statistics, total revenue, and active bookings.
- **User Management:** Verify pending providers, update user details, or remove accounts.
- **Total Control:** Monitor all transactions and parking activities across the platform.

---

## 💻 Tech Stack

- **Backend:** Python 3, Flask, SQLAlchemy (ORM)
- **Database:** SQLite (`smartpark.db`)
- **Frontend:** HTML5, CSS3, JavaScript, Jinja2 Templates
- **Computer Vision:** OpenCV (`core.detector`)
- **Integrations:**
  - **Payments:** Razorpay API
  - **Notifications:** Twilio API (SMS & WhatsApp)
  - **QR Generation:** Python `qrcode` library

---

## 🚀 Installation & Setup

Follow these steps to run the project locally.

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/SmartPark-Flask.git
cd SmartPark-Flask/SmartPark_Flask
```

### 2. Set up a Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Ensure your `config.py` is correctly set up. You will need to add your API keys for Razorpay and Twilio. If you don't have them yet, the app includes fallback mock mechanisms for testing!

Example `.env` or `config.py` setup:
```python
SECRET_KEY = "your-secret-key"
RAZORPAY_KEY_ID = "YOUR_KEY"
RAZORPAY_KEY_SECRET = "YOUR_SECRET"
TWILIO_SID = "YOUR_TWILIO_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_TOKEN"
TWILIO_PHONE_NUMBER = "+1234567890"
```

### 5. Run the Application
```bash
python app.py
```
The application will be running at `http://127.0.0.1:5000/`. The database (`smartpark.db`) will be automatically created on the first run.

---

## 📘 Workflows & Architecture

The project includes pre-rendered system design files. You can open these HTML files in your browser to understand the architecture:
- `data_flow_diagram.html` - System Data Flow
- `classic_er_diagram.html` / `chen_er_diagram.html` - Entity Relationship Diagrams
- `system_diagram_render.html` - High-level Architecture

---

## 📸 Sample Images

<p align="center">
  <i>(Replace these temporary links with actual screenshots from your running app)</i><br>
  <img src="https://images.unsplash.com/photo-1506521781263-284ceab30026?q=80&w=800&auto=format&fit=crop" width="45%" style="border-radius: 10px; margin: 10px;">
  <img src="https://images.unsplash.com/photo-1474408886716-087263db7a60?q=80&w=800&auto=format&fit=crop" width="45%" style="border-radius: 10px; margin: 10px;">
</p>

---

## 🛡️ License

This project is licensed under the MIT License - see the LICENSE file for details.

---
<div align="center">
  <b>Built with ❤️ for a smarter future of parking.</b>
</div>
