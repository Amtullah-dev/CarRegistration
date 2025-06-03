import os


class Config:
    # Basic Flask settings
    SECRET_KEY = 'your-secret-key'

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cars.db'

    # JWT settings
    JWT_SECRET_KEY = 'your-jwt-secret'

    # Parse settings
    PARSE_APP_ID = 'hlhoNKjOvEhqzcVAJ1lxjicJLZNVv36GdbboZj3Z'
    PARSE_API_KEY = 'SNMJJF0CZZhTPhLDIqGhTlUNV9r60M2Z5spyWfXW'

    # Celery settings
    CELERY_BROKER_URL = 'filesystem://'
    CELERY_RESULT_BACKEND = 'file://./celery_results'
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'data_folder_in': './celery_data/out',
        'data_folder_out': './celery_data/out',
        'data_folder_processed': './celery_data/processed',
    }
