from sqlalchemy import Column, Integer, String, Boolean
from car_registration.models.base import Base


class Test(Base):

    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)
    working = Column(Boolean)
