from car_sync_celery import app, db

with app.app_context():
    db.create_all()
    print("✅ Database initialized successfully.")
