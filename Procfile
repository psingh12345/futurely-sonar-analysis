web: gunicorn --bind :8000 thefuturely.wsgi:application
celery_worker: celery -A thefuturely worker --loglevel=info --concurrency=4
celery_beat: celery -A thefuturely beat -l info -S django