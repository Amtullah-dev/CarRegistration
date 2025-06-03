import logging
import os
import requests

from flask import current_app
from config import Config
from tasks.celery.celery_config import create_celery
from models.car_model import db, Car

# Configure logging
logger = logging.getLogger(__name__)

# Create Celery instance without Flask app
celery = create_celery(__name__)


@celery.task(name='car_sync_celery.sync_car_data_task')
def sync_car_data_task():
    """
    Celery task to sync car data from external API.
    Uses Flask application context from the main app.
    """
    try:
        url = "https://parseapi.back4app.com/classes/Car_Model_List"
        headers = {
            "X-Parse-Application-Id": Config.PARSE_APP_ID,
            "X-Parse-REST-API-Key": Config.PARSE_API_KEY
        }
        params = {"limit": 100, "skip": 0}
        added = 0

        while True:
            r = requests.get(url, headers=headers, params=params)

            if r.status_code != 200:
                logger.error(
                    f"API request failed with status code {r.status_code}: {r.text}"
                )
                break

            data = r.json().get("results", [])
            if not data:
                logger.info("No more data to fetch, pagination complete")
                break

            for car in data:
                make = car.get("Make", "").strip()
                model = car.get("Model", "").strip()
                year = car.get("Year")

                logger.debug(f"Processing car: {make}")

                if not (make and model and year):
                    continue

                year = int(year)
                exists = Car.query.filter_by(
                    make=make, model=model, year=year
                ).first()
                if not exists:
                    db.session.add(Car(make=make, model=model, year=year))
                    added += 1

            db.session.commit()
            logger.debug(f"Processed batch, added {added} cars so far")
            params["skip"] += params["limit"]

        logger.info(f"Added {added} new cars.")
        return {"status": "success", "added": added}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in sync_car_data_task: {str(e)}")
        return {"status": "error", "message": str(e)}


def sync_car_data_function():
    """
    Direct function version for synchronous execution.
    Uses current Flask application context.
    """
    try:
        url = "https://parseapi.back4app.com/classes/Car_Model_List"
        headers = {
            "X-Parse-Application-Id": Config.PARSE_APP_ID,
            "X-Parse-REST-API-Key": Config.PARSE_API_KEY
        }
        params = {"limit": 100, "skip": 0}
        added = 0

        while True:
            r = requests.get(url, headers=headers, params=params)

            if r.status_code != 200:
                logger.error(
                    f"API request failed with status code {r.status_code}: {r.text}"
                )
                break

            data = r.json().get("results", [])
            if not data:
                logger.info("No more data to fetch, pagination complete")
                break

            for car in data:
                make = car.get("Make", "").strip()
                model = car.get("Model", "").strip()
                year = car.get("Year")

                if not (make and model and year):
                    continue

                year = int(year)
                exists = Car.query.filter_by(
                    make=make, model=model, year=year
                ).first()
                if not exists:
                    db.session.add(Car(make=make, model=model, year=year))
                    added += 1

            db.session.commit()
            logger.debug(f"Processed batch, added {added} cars so far")
            params["skip"] += params["limit"]

        logger.info(f"Added {added} new cars.")
        return {"status": "success", "added": added}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in sync_car_data_function: {str(e)}")
        return {"status": "error", "message": str(e)}
