import logging
from celery import Celery
from config import Config
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

celery = Celery('celery_app')

celery.conf.update(
    broker_url='redis://redis:6379/0',
    result_backend='redis://redis:6379/1',
)

celery.conf.beat_schedule = {
    # 'sync-cars-every-5-minutes': {
    #     'task': 'car_registration.tasks.car_tasks.sync_cars_with_celery.sync_car_data',
    #     'schedule': crontab(minute='*/5'),
    # },
    'sync-car-data-every-2-minutes': {
        'task': 'car_registration.tasks.car_tasks.client_sync_request_task.client_sync_request_task',
        'schedule': 120.0,
    },
}

celery.autodiscover_tasks([
                            'car_registration.tasks.car_tasks.sync_cars_with_celery',
                            'car_registration.tasks.car_tasks.client_sync_request_task',
                            'car_registration.tasks.car_tasks.sync_car_data_task',
                           'car_registration.tasks',
                           ])

import car_registration.tasks.car_tasks.client_sync_request_task
# import car_registration.tasks.car_tasks.sync_cars_with_celery
import car_registration.tasks.car_tasks.sync_car_data_task
