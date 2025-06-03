# # car_sync_celery.py
# import os
# import requests
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from celery import Celery
# from celery.schedules import crontab
# from dotenv import load_dotenv

# # Load .env
# load_dotenv()

# # Flask setup
# app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///cars.db")
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# db = SQLAlchemy(app)

# # Celery setup with SQLite broker and backend
# celery = Celery(__name__,
#     broker='sqla+sqlite:///celery_broker.sqlite',
#     backend='db+sqlite:///celery_results.sqlite'
# )
# # celery.conf.timezone = 'UTC'
# celery.conf.timezone = 'Asia/Karachi'

# # Celery Beat: run task every day at 2 AM
# celery.conf.beat_schedule = {
#     'sync-cars-daily-2am': {
#         'task': 'car_sync_celery.sync_car_data_task',
#         'schedule': crontab(hour=11, minute=35),
#     }
# }

# # Car model
# class Car(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     make = db.Column(db.String(100))
#     model = db.Column(db.String(100))
#     year = db.Column(db.Integer)

# # Task to fetch and save car data
# # @celery.task
# @celery.task(name='car_sync_celery.sync_car_data_task')
# def sync_car_data_task():
#     with app.app_context():
#         try:
#             url = "https://parseapi.back4app.com/classes/Car_Model_List"
#             headers = {
#                 "X-Parse-Application-Id": os.getenv("PARSE_APP_ID"),
#                 "X-Parse-REST-API-Key": os.getenv("PARSE_API_KEY")
#             }
#             params = {"limit": 100, "skip": 0}
#             added = 0

#             while True:
#                 r = requests.get(url, headers=headers, params=params)
#                 data = r.json().get("results", [])
#                 if not data:
#                     break

#                 for car in data:
#                     make = car.get("Make", "").strip()
#                     model = car.get("Model", "").strip()
#                     year = car.get("Year")
#                     print(make)

#                     if not (make and model and year):
#                         continue

#                     year = int(year)
#                     exists = Car.query.filter_by(make=make, model=model, year=year).first()
#                     if not exists:
#                         db.session.add(Car(make=make, model=model, year=year))
#                         added += 1

#                 db.session.commit()
#                 params["skip"] += params["limit"]

#             print(f"Added {added} new cars.")
#         except Exception as e:
#             db.session.rollback()
#             print(f"Error syncing cars: {e}")



# car_sync_celery.py
import os
import requests
from flask import Flask
from dotenv import load_dotenv

# Import from separated modules
from celery_config import create_celery
from car_model import db, Car

# Load .env
load_dotenv()

# Flask setup
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///cars.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# Create Celery instance
celery = create_celery(__name__)

# Task to fetch and save car data
@celery.task(name='car_sync_celery.sync_car_data_task')
def sync_car_data_task():
    with app.app_context():
        try:
            url = "https://parseapi.back4app.com/classes/Car_Model_List"
            headers = {
                "X-Parse-Application-Id": os.getenv("PARSE_APP_ID"),
                "X-Parse-REST-API-Key": os.getenv("PARSE_API_KEY")
            }
            params = {"limit": 100, "skip": 0}
            added = 0

            while True:
                r = requests.get(url, headers=headers, params=params)
                data = r.json().get("results", [])
                if not data:
                    break

                for car in data:
                    make = car.get("Make", "").strip()
                    model = car.get("Model", "").strip()
                    year = car.get("Year")
                    print(make)

                    if not (make and model and year):
                        continue

                    year = int(year)
                    exists = Car.query.filter_by(make=make, model=model, year=year).first()
                    if not exists:
                        db.session.add(Car(make=make, model=model, year=year))
                        added += 1

                db.session.commit()
                params["skip"] += params["limit"]

            print(f"Added {added} new cars.")
        except Exception as e:
            db.session.rollback()
            print(f"Error syncing cars: {e}")