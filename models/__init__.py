from flask_sqlalchemy import SQLAlchemy

# Define db only – don't import app or models here!
db = SQLAlchemy()

from .user_model import User
from .car_model import Car
