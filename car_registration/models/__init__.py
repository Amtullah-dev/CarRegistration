from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user_model import User
from .car_model import Car
