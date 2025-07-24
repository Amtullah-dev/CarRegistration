from sqlalchemy import Column, Integer, String
from car_registration.models.base import Base


class Car(Base):

    __tablename__ = 'car'

    id = Column(Integer, primary_key=True)
    make = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
