from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, JSON, Float, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class RagEvent(Base):
    __tablename__ = 'rag_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query: Mapped[str] = mapped_column(Text)
    query_type: Mapped[str] = mapped_column(String(40))
    evidence_ids = mapped_column(JSON, nullable=False)
    citation_ids = mapped_column(JSON, nullable=False)
    model_name: Mapped[str] = mapped_column(String(255))
    model_version: Mapped[str] = mapped_column(String(100))
    latency_ms: Mapped[int] = mapped_column(Integer)
    coverage: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    insufficient_evidence: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
