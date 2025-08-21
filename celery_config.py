from celery import Celery
import os

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Celery configuration
CELERY_CONFIG = {
    'broker_url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'result_backend': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30 minutes
    'task_soft_time_limit': 25 * 60,  # 25 minutes
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
}

# Task routing
CELERY_ROUTES = {
    'ml_services.analyze_journal_entry': {'queue': 'ml_tasks'},
    'ml_services.batch_analyze_entries': {'queue': 'ml_tasks'},
}

# Task queues
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = {
    'default': {},
    'ml_tasks': {
        'exchange': 'ml_tasks',
        'routing_key': 'ml_tasks',
    },
}







