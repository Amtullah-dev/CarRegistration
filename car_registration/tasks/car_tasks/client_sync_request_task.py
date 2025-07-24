import logging
from datetime import datetime

from car_registration.tasks.celery_app import celery
from car_registration.grpc.client import CarSyncClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.task(name='car_registration.tasks.car_tasks.client_sync_request_task.client_sync_request_task')
def client_sync_request_task():

    try:
        client = CarSyncClient()
        response = client.sync_car_data()

        if response:
            logger.info(f"Sync successful at {datetime.now()}")
            return {
                "status": response.status,
                "total_count": response.total_count,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("No response received from server")
            return {"status": "error", "error": "No response received"}

    except Exception as e:
        logger.error(f"Client sync task failed: {e}")
        return {"status": "error", "error": str(e)}
