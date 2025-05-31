import os
from celery.schedules import crontab

class CeleryConfig:
    """Base Celery configuration"""
    broker_url = 'sqla+sqlite:///celery_broker.db'
    result_backend = 'db+sqlite:///celery_results.db'
    timezone = 'UTC'
    
    # Task serialization
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    
    # Task routing and execution
    task_always_eager = False
    task_eager_propagates = True
    task_routes = {
        'celery_worker_sqlite.sync_car_data_task': {'queue': 'car_sync'},
    }
    
    # Worker configuration
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 1000
    
    # Beat schedule configuration
    beat_schedule = {
        'sync-car-data-daily': {
            'task': 'celery_worker_sqlite.sync_car_data_task',
            'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM UTC (7 PM PST)
        },
    }
    
    # API configuration
    API_CONFIG = {
        'url': "https://parseapi.back4app.com/classes/Car_Model_List",
        'headers': {
            "X-Parse-Application-Id": os.environ.get('PARSE_APP_ID', "hlhoNKjOvEhqzcVAJ1lxjicJLZNVv36GdbboZj3Z"),
            "X-Parse-REST-API-Key": os.environ.get('PARSE_API_KEY', "SNMJJF0CZZhTPhLDIqGhTlUNV9r60M2Z5spyWfXW")
        },
        'batch_size': 1000,
        'timeout': 30
    }
    
    # Data validation configuration
    DATA_CONFIG = {
        'year_range': (2012, 2022),
        'required_fields': ['Make', 'Model', 'Year'],
        'batch_commit_size': 100
    }

class CeleryDevelopmentConfig(CeleryConfig):
    """Development Celery configuration"""
    task_always_eager = True  # Execute tasks synchronously in development
    broker_url = 'sqla+sqlite:///celery_broker_dev.db'
    result_backend = 'db+sqlite:///celery_results_dev.db'

class CeleryProductionConfig(CeleryConfig):
    """Production Celery configuration"""
    # Use environment variables for sensitive data
    API_CONFIG = {
        'url': "https://parseapi.back4app.com/classes/Car_Model_List",
        'headers': {
            "X-Parse-Application-Id": os.environ.get('PARSE_APP_ID'),
            "X-Parse-REST-API-Key": os.environ.get('PARSE_API_KEY')
        },
        'batch_size': 1000,
        'timeout': 30
    }
    
    # Validate required environment variables
    if not API_CONFIG['headers']["X-Parse-Application-Id"] or not API_CONFIG['headers']["X-Parse-REST-API-Key"]:
        raise ValueError("PARSE_APP_ID and PARSE_API_KEY must be set in production")
    
    # Production optimizations
    worker_prefetch_multiplier = 4
    worker_concurrency = 4

class CeleryTestingConfig(CeleryConfig):
    """Testing Celery configuration"""
    task_always_eager = True
    broker_url = 'sqla+sqlite:///:memory:'
    result_backend = 'db+sqlite:///:memory:'

# Configuration dictionary
celery_config = {
    'development': CeleryDevelopmentConfig,
    'production': CeleryProductionConfig,
    'testing': CeleryTestingConfig,
    'default': CeleryDevelopmentConfig
}