from app.database import db

# from flask_sqlalchemy import SQLAlchemy

# # Define db only – don't import app or models here!
# db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)