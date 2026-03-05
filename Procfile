web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
worker: cd backend && celery -A app.worker.tasks worker --loglevel=info --concurrency=2
beat: cd backend && celery -A app.worker.tasks beat --loglevel=info
