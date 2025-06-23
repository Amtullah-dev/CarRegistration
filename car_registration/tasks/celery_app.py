import logging
import requests
from celery import Celery
from celery.schedules import crontab
from config import Config
from car_registration.models.car_model import Car
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

@contextmanager
def get_db_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Create Celery instance
celery = Celery('celery_app')

celery.conf.update(
    # broker_url='sqla+sqlite:///celery_broker.sqlite',
    # result_backend='db+sqlite:///celery_results.sqlite',
    broker_url='redis://redis:6379/0',
    result_backend='redis://redis:6379/1',
)

# Schedule the task to run every 5 minutes
celery.conf.beat_schedule = {
    'sync-cars-every-5-minutes': {
        'task': 'car_registration.tasks.car_tasks.sync_cars_with_celery.sync_car_data',
        'schedule': crontab(minute='*/5'),
    },
}

celery.autodiscover_tasks(['car_registration.tasks.car_tasks.sync_cars_with_celery'])
