from contextlib import contextmanager
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apiflask import APIFlask

from config import Config
from car_registration.models import db
from car_registration.web import register_routes

from apiflask import APIFlask, Schema
from apiflask.fields import String, Integer, Field

app = APIFlask(__name__)

# class BaseResponse(Schema):
#     data = Field()  # the data key
#     message = String()
#     code = Integer()
#
# app.config['BASE_RESPONSE_SCHEMA'] = BaseResponse
# app.config['BASE_RESPONSE_DATA_KEY '] = 'data'
app.config['BASE_RESPONSE_SCHEMA'] = None  # No base response wrapping
app.config['BASE_RESPONSE_DATA_KEY'] = 'data'
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
register_routes(app)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
# For example in app.py or wherever you initialize your app
# from car_registration.web.users.schemas import BaseResponseSchema

# app.config['BASE_RESPONSE_SCHEMA'] = BaseResponseSchema

@contextmanager
def get_db_session():
    db_session = Session()
    try:
        yield db_session
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
    finally:
        db_session.close()

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, host='0.0.0.0', port=5000)
