import logging
import requests
from car_registration.tasks.celery_app import get_db_session
from config import Config
from car_registration.models.car_model import Car
from car_registration.tasks.celery_app import celery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.task(name='car_registration.tasks.car_tasks.sync_cars_with_celery.sync_car_data')
def sync_car_data():
    """Sync car data from external API every 5 minutes"""
    logger.info("Starting car data sync...")
    
    url = "https://parseapi.back4app.com/classes/Car_Model_List"
    headers = {
        "x-parse-application-id": Config.PARSE_APP_ID,
        "x-parse-master-key": Config.PARSE_API_KEY
    }
    params = {"limit": 100, "skip": 0}
    added = 0

    try:
        with get_db_session() as session:
            while True:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.status_code}")
                    break

                data = response.json().get("results", [])
                if not data:
                    break

                for car in data:
                    make = car.get("Make", "").strip()
                    model = car.get("Model", "").strip()
                    year = car.get("Year")

                    if not (make and model and year):
                        continue

                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        continue
                        
                    # Check if car already exists
                    exists = session.query(Car).filter_by(
                        make=make, model=model, year=year
                    ).first()
                    
                    if not exists:
                        session.add(Car(make=make, model=model, year=year))
                        added += 1

                params["skip"] += params["limit"]

        logger.info(f"Car sync with Database completed. Added {added} new cars.")
        return {"status": "success", "added": added}
        
    except Exception as e:
        logger.error(f"Error syncing car data: {e}")
        raise



    