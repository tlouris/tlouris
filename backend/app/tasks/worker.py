from celery import Celery

from app.core.config import settings

celery_app = Celery("flow-monitor", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "UTC"


@celery_app.task
def run_nightly_anomaly_job():
    """Placeholder for nightly batch orchestration per meter."""
    return {"status": "queued-meter-runs"}
