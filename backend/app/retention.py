import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import delete, select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.retrieval import RetrievalEvent
from app.models.rag import RagEvent
from app.models.evaluation import EvaluationResult

log=logging.getLogger(__name__)
def cleanup():
    if settings.RETENTION_DAYS <= 0: return 0
    db=SessionLocal(); deleted=0
    try:
        cutoff=datetime.now(timezone.utc)-timedelta(days=settings.RETENTION_DAYS)
        docs=db.scalars(select(Document).where(Document.created_at < cutoff)).all()
        for d in docs:
            path=Path(d.file_path); db.delete(d); path.unlink(missing_ok=True); deleted+=1
        db.execute(delete(RetrievalEvent).where(RetrievalEvent.created_at < cutoff))
        db.execute(delete(RagEvent).where(RagEvent.created_at < cutoff))
        db.execute(delete(EvaluationResult).where(EvaluationResult.created_at < cutoff))
        db.commit(); return deleted
    except Exception:
        db.rollback(); log.exception("Retention cleanup failed")
        return 0
    finally: db.close()
