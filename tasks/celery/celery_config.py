from celery import Celery
from celery.schedules import crontab


def create_celery(app_name):
    celery = Celery(
        app_name,
        broker='sqla+sqlite:///celery_broker.sqlite',
        backend='db+sqlite:///celery_results.sqlite'
    )

    # Set timezone
    celery.conf.timezone = 'Asia/Karachi'

    # Define periodic task schedule
    celery.conf.beat_schedule = {
        'sync-cars-daily-2am': {
            'task': 'car_sync_celery.sync_car_data_task',
            'schedule': crontab(hour=11, minute=35),
        }
    }

    return celery
