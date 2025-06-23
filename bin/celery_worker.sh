#!/usr/bin/env bash
 celery -A car_registration.tasks.celery_app worker --loglevel=info --pool=solo
