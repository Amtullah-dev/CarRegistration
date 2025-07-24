import logging

from car_registration.tasks.celery_app import celery
from car_registration.web.cars.api import sync_car_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery.task(name='car_registration.tasks.car_tasks.sync_car_data_task')
def sync_car_data_task():
    """Celery task wrapper for car data sync"""

    try:
        result = sync_car_data()
        # logger.info(f"Task completed: {len(result.get('car_list', []))} cars synced")
        return result
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return {"status": "error", "cars": [], "error": str(e)}


