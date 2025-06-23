from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from car_registration.models.car_model import Car
from car_registration.web.cars.schemas import CarSchema
from car_registration.models.database import db  # Add this import

car_bp = Blueprint('cars', __name__)

# Schemas
car_schema = CarSchema()
cars_schema = CarSchema(many=True)


@car_bp.route('/sync-cars', methods=['POST'])
@jwt_required()
def sync_cars():
    """
    Manual trigger for car data synchronization
    Requires JWT authentication
    """
    celery = current_app.extensions.get('celery')
    
    if celery is None:
        try:
            # from car_registration.tasks.car_tasks.sync_cars_with_celery import sync_car_data_function
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


@car_bp.route('/cars', methods=['GET'])
@jwt_required()
def get_cars():
    """
    Search and filter cars
    Query parameters:
    - make: Filter by car make (partial match)
    - model: Filter by car model (partial match)
    - year: Filter by exact year
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    """
    make = request.args.get('make', '').strip()
    model = request.args.get('model', '').strip()
    year = request.args.get('year', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    if page < 1:
        return jsonify({"message": "Page must be greater than 0"}), 400
    if per_page < 1:
        return jsonify({"message": "Per page must be greater than 0"}), 400
    
    try:
        query = db.session.query(Car)  
        
        if make:
            query = query.filter(Car.make.ilike(f"%{make}%"))
        if model:
            query = query.filter(Car.model.ilike(f"%{model}%"))
        if year:
            if year < 2012 or year > 2022:
                return jsonify({
                    "message": "Year must be between 2012 and 2022"
                }), 400
            query = query.filter_by(year=year)
        
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        response = {
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": per_page,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
            "cars": cars_schema.dump(paginated.items)
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({"message": f"Search failed: {str(e)}"}), 500
    