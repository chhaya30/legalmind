
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(30))
    query: Mapped[str] = mapped_column(Text)
    mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    relevant_ids = mapped_column(JSON, nullable=True)
    expected_keywords = mapped_column(JSON, nullable=True)
    held_out: Mapped[bool] = mapped_column(default=False)
    metadata_json = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    case_id: Mapped[str] = mapped_column(String(100), index=True)
    metric: Mapped[str] = mapped_column(String(80))
    value: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
