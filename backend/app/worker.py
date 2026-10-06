from redis import Redis
from rq import Queue, Worker
from app.core.config import settings
import threading, time
from app.retention import cleanup

def retention_loop():
    while True:
        cleanup(); time.sleep(3600)

if __name__ == "__main__":
    threading.Thread(target=retention_loop, daemon=True).start()
    redis = Redis.from_url(settings.REDIS_URL)
    Worker([Queue(name=settings.WORKER_QUEUE, connection=redis)], connection=redis).work()
