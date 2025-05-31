from app.database import db


# from flask_sqlalchemy import SQLAlchemy

# # Define db only – don't import app or models here!
# db = SQLAlchemy()

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)