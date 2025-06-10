import logging

from tasks.celery_app import app, db

logger = logging.getLogger(__name__)

with app.app_context():
    db.create_all()
    logger.info("Database initialized successfully.")
