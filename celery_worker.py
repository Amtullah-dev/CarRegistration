# celery_worker.py
from celery import Celery
from celery.schedules import crontab
import requests
import os

def make_celery(app):
    """
    Create and configure Celery instance
    """
    # Create directories for filesystem broker if they don't exist
    os.makedirs('./celery_data/out', exist_ok=True)
    os.makedirs('./celery_data/processed', exist_ok=True)
    os.makedirs('./celery_results', exist_ok=True)
    
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'],
        broker_transport_options=app.config['CELERY_BROKER_TRANSPORT_OPTIONS']
    )
    
    # Update Celery config from Flask config
    celery.conf.update(app.config)
    
    # Configure periodic tasks
    celery.conf.beat_schedule = {
        'sync-car-data-daily': {
            'task': 'celery_worker.sync_car_data_task',
            'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM
        },
    }
    celery.conf.timezone = 'UTC'
    
    # Ensure tasks run within Flask app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery


# Create Celery instance (this will be imported by app.py)
from flask import Flask
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'filesystem://'
app.config['CELERY_RESULT_BACKEND'] = 'file://./celery_results'
app.config['CELERY_BROKER_TRANSPORT_OPTIONS'] = {
    'data_folder_in': './celery_data/out',
    'data_folder_out': './celery_data/out',
    'data_folder_processed': './celery_data/processed',
}

celery = make_celery(app)


def sync_car_data_function():
    """
    Core function to sync car data from API
    This can be called directly or as a Celery task
    """
    from models import db, Car
    
    url = "https://parseapi.back4app.com/classes/Car_Model_List"
    headers = {
        "X-Parse-Application-Id": "hlhoNKjOvEhqzcVAJ1lxjicJLZNVv36GdbboZj3Z",
        "X-Parse-REST-API-Key": "SNMJJF0CZZhTPhLDIqGhTlUNV9r60M2Z5spyWfXW"
    }
    
    try:
        print("Starting car data synchronization...")
        
        # Fetch data from API with pagination
        all_cars = []
        skip = 0
        limit = 1000  # Batch size
        
        while True:
            params = {
                'limit': limit,
                'skip': skip,
                'keys': 'Make,Model,Year'  # Only fetch required fields
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"API request failed with status {response.status_code}")
                break
                
            data = response.json().get("results", [])
            
            if not data:  # No more data
                break
                
            all_cars.extend(data)
            skip += limit
            
            print(f"Fetched {len(all_cars)} cars so far...")
            
            # Safety check to prevent infinite loop
            if len(data) < limit:
                break
        
        print(f"Total cars fetched from API: {len(all_cars)}")
        
        # Process and store data
        cars_added = 0
        cars_updated = 0
        cars_skipped = 0
        
        for item in all_cars:
            try:
                # Validate required fields
                make = item.get("Make", "").strip()
                model = item.get("Model", "").strip()
                year_str = item.get("Year")
                
                if not make or not model or not year_str:
                    cars_skipped += 1
                    continue
                
                # Validate and convert year
                try:
                    year = int(year_str)
                except (ValueError, TypeError):
                    cars_skipped += 1
                    continue
                
                # Filter by year range (2012-2022)
                if not (2012 <= year <= 2022):
                    cars_skipped += 1
                    continue
                
                # Check if car already exists
                existing_car = Car.query.filter_by(
                    make=make, 
                    model=model, 
                    year=year
                ).first()
                
                if existing_car:
                    # Car already exists - you could update here if needed
                    cars_skipped += 1
                    continue
                else:
                    # Add new car
                    new_car = Car(make=make, model=model, year=year)
                    db.session.add(new_car)
                    cars_added += 1
                
                # Commit in batches to avoid memory issues
                if (cars_added + cars_updated) % 100 == 0:
                    db.session.commit()
                    
            except Exception as e:
                print(f"Error processing car {item}: {str(e)}")
                cars_skipped += 1
                continue
        
        # Final commit
        db.session.commit()
        
        result = {
            "status": "success",
            "cars_added": cars_added,
            "cars_updated": cars_updated,
            "cars_skipped": cars_skipped,
            "total_processed": len(all_cars)
        }
        
        print(f"Car data sync completed: {result}")
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during car data sync: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error during car data sync: {str(e)}"
        print(error_msg)
        db.session.rollback()
        return {"status": "error", "message": error_msg}


@celery.task(bind=True, name='celery_worker.sync_car_data_task')
def sync_car_data_task(self):
    """
    Celery task for syncing car data
    This task can be called manually or scheduled
    """
    try:
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Starting car data synchronization...', 'current': 0, 'total': 100}
        )
        
        # Initialize Flask app context for database operations
        from app import app
        with app.app_context():
            # Import here to avoid circular imports
            from models import db
            
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Fetching data from API...', 'current': 25, 'total': 100}
            )
            
            result = sync_car_data_function()
            
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Data sync completed', 'current': 100, 'total': 100}
            )
            
            return result
            
    except Exception as e:
        # Task failed
        self.update_state(
            state='FAILURE',
            meta={'status': f'Task failed: {str(e)}', 'error': str(e)}
        )
        raise e


if __name__ == '__main__':
    # This allows running the worker directly
    celery.start()