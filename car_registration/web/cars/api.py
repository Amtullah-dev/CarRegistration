import logging

import requests
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from car_registration.models.car_model import Car
from car_registration.web.cars.schemas import CarSchema
from car_registration.models import db
from config import Config
from celery.result import AsyncResult
from car_registration.tasks.celery_app import celery
from car_registration.web.users.validation import validate_json
from car_registration.web.cars.schemas import SyncCarsInputSchema, SyncCarsOutputSchema, TaskResultOutputSchema

cars_bp = Blueprint('cars_bp', __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@cars_bp.route('/sync-cars', methods=['POST'])
@jwt_required()
@validate_json(SyncCarsInputSchema)
@validate_json(SyncCarsOutputSchema)
def sync_cars():

    celery = current_app.extensions.get('celery')
    
    if celery is None:
        try:
            from car_registration.tasks.car_tasks.sync_cars_with_celery import sync_car_data
            result = sync_car_data()
            return jsonify({
                "message": "Car data sync completed (direct execution)",
                "result": result
            }), 200
        except Exception as e:
            return jsonify({"message": f"Sync failed: {str(e)}"}), 500
    
    try:
        from car_registration.tasks.car_tasks.sync_cars_with_celery import sync_car_data
        task = sync_car_data.delay()
        return jsonify({
            "message": "Car data sync initiated",
            "task_id": task.id
        }), 200
    except Exception as e:
        return jsonify({"message": f"Failed to initiate sync: {str(e)}"}), 500

#for the celery task
def sync_car_data():
    """Fetch car data from API aand return as list"""
    logger.info("Starting car data sync...")
    url = "https://parseapi.back4app.com/classes/Car_Model_List"
    headers = {
        "X-Parse-Application-Id": Config.PARSE_APP_ID,
        "x-parse-master-key": Config.PARSE_API_KEY
    }
    params = {"limit": 100, "skip": 0}
    car_list = []
    try:
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
                car_list.append({
                    "make": make,
                    "model": model,
                    "year": year
                })
            params["skip"] += params["limit"]
        logger.info(f"Car sync completed. Retrieved {len(car_list)} cars.")
        # return {"status": "success", "cars": car_list}
        return {"status": "success. Cars Synced"}

    except Exception as e:
        logger.error(f"Error syncing car data: {e}")
        raise

def get_task_result(task_id):
    result = AsyncResult(task_id, app=celery)
    if result.ready():
        return result.result
    else:
        return {"status": "pending"}

@cars_bp.route('/sync/result/<task_id>', methods=['POST'])
@validate_json(TaskResultOutputSchema)

def task_result(task_id):
    result = get_task_result(task_id)
    return jsonify(result)
