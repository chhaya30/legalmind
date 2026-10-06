
from redis import Redis
from rq import Queue
from app.core.config import settings

def enqueue_document(document_id: str):
    q=Queue(settings.WORKER_QUEUE, connection=Redis.from_url(settings.REDIS_URL))
    return q.enqueue("app.services.processor.process_document", document_id)
