from app import app
from database.models import db, User, ParkingLot

def init_db():
    """
    Creates the database tables and populates them with initial dummy data.
    """
    with app.app_context():
        # 1. Create all tables defined in models.py
        db.create_all()
        print("✅ Database tables created successfully!")

        # 2. Check if we already have an Admin user
        if not User.query.filter_by(uname='admin').first():
            admin = User(
                uname='admin',
                name='Admin User',
                mobile='0000000000',
                email='admin@example.com',
                location='HQ',
                password='adminpassword', # In a real app, hash this!
                role='admin'
            )
            db.session.add(admin)
            print("👤 Admin user created (User: admin / Pass: adminpassword)")

        # 3. Check if we already have a Provider user
        if not User.query.filter_by(uname='provider').first():
            provider = User(
                uname='provider',
                name='Provider User',
                mobile='1111111111',
                email='provider@example.com',
                location='City Center',
                password='providerpass',
                role='provider'
            )
            db.session.add(provider)
            print("👤 Provider user created (User: provider / Pass: providerpass)")

        # 4. Commit changes
        db.session.commit()
        print("✅ Database initialization complete.")

if __name__ == '__main__':
    init_db()