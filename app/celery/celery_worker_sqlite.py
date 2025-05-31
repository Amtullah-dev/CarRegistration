# celery_worker_sqlite.py
from dotenv import load_dotenv
load_dotenv()
from celery import Celery
from app.celery.celery_config import celery_config
import requests
import os




def make_celery(app):
    """Create Celery instance with Flask app context"""
    # Get config name from environment or use default
    config_name = os.environ.get('FLASK_ENV', 'default')
    config_class = celery_config[config_name]
    
    celery = Celery(
        app.import_name,
        broker=config_class.broker_url,
        backend=config_class.result_backend
    )
    
    # Apply Celery configuration
    celery.config_from_object(config_class)
    
    # Override with Flask app config if needed
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Create Celery instance
from flask import Flask
app = Flask(__name__)
celery = make_celery(app)


def sync_car_data_function():
    """
    Core function to sync car data from API
    This can be called directly or as a Celery task
    """
    try:
        from app.models.user_model import db, Car
    except ImportError:
        print("Error: models.py not found or Car model not defined")
        return {"status": "error", "message": "Database models not available"}
    
    # Get configuration
    config_name = os.environ.get('FLASK_ENV', 'default')
    config_class = celery_config[config_name]
    api_config = config_class.API_CONFIG
    data_config = config_class.DATA_CONFIG
    
    try:
        print("Starting car data synchronization...")
        
        # Fetch data from API with pagination
        all_cars = []
        skip = 0
        limit = api_config['batch_size']
        
        while True:
            params = {
                'limit': limit,
                'skip': skip,
                'keys': ','.join(data_config['required_fields'])
            }
            
            response = requests.get(
                api_config['url'], 
                headers=api_config['headers'], 
                params=params, 
                timeout=api_config['timeout']
            )
            
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
        min_year, max_year = data_config['year_range']
        
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
                
                # Filter by year range
                if not (min_year <= year <= max_year):
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
                if (cars_added + cars_updated) % data_config['batch_commit_size'] == 0:
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
        try:
            db.session.rollback()
        except:
            pass
        return {"status": "error", "message": error_msg}


@celery.task(bind=True, name='celery_worker_sqlite.sync_car_data_task')
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


celery_app = celery