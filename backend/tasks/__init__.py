"""
Celery tasks module for background processing.

This module sets up the Celery application for running background tasks
such as computing indicators and generating signals.
"""

from celery import Celery
from celery.schedules import crontab
import logging
import os

# Import configuration
from backend.settings import get_config

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Create Celery app
celery_app = Celery(
    'trading_manager',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=['backend.tasks.indicators', 'backend.tasks.signals']
)

# Configure Celery
celery_app.conf.update(
    task_serializer=config.CELERY_TASK_SERIALIZER,
    result_serializer=config.CELERY_RESULT_SERIALIZER,
    accept_content=config.CELERY_ACCEPT_CONTENT,
    timezone=config.CELERY_TIMEZONE,
    enable_utc=config.CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Configure Celery Beat schedule (only if enabled)
if config.CELERY_ENABLE_BEAT:
    celery_app.conf.beat_schedule = config.CELERY_BEAT_SCHEDULE
    logger.info("Celery Beat scheduling enabled")
else:
    logger.info("Celery Beat scheduling disabled (set CELERY_ENABLE_BEAT=true to enable)")

# Task routes (optional - for routing tasks to specific queues)
celery_app.conf.task_routes = {
    'backend.tasks.indicators.*': {'queue': 'indicators'},
    'backend.tasks.signals.*': {'queue': 'signals'},
}

logger.info(f"Celery app initialized with broker: {config.CELERY_BROKER_URL}")


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    logger.info(f'Request: {self.request!r}')
    return 'Debug task completed'
