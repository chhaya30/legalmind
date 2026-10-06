from datetime import datetime
from sqlalchemy import String, Text, Integer, BigInteger, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.db.base import Base

EMBEDDING_DIM = 768

class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), unique=True, index=True)
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255))
    dimension: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RetrievalEvent(Base):
    __tablename__ = "retrieval_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(30))
    filters = mapped_column(JSON, nullable=True)
    retrieved_ids = mapped_column(JSON, nullable=False)
    reranked_ids = mapped_column(JSON, nullable=False)
    latency_ms: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
