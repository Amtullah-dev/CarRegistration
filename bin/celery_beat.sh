#!/usr/bin/env bash
 celery -A car_registration.tasks.celery_app beat --loglevel=info
