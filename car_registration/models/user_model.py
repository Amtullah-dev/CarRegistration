from sqlalchemy import Column, Integer, String
from car_registration.models.base import Base


class User(Base):

    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    password = Column(String(100))
    