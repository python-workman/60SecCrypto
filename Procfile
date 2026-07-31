web: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
worker: celery -A app.tasks.celery_app.celery_app worker --loglevel=info
beat: celery -A app.tasks.celery_app.celery_app beat --loglevel=info