# car_model.py
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

class Car(db.Model):
    """Car model for storing vehicle information"""
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Car {self.make} {self.model} {self.year}>'