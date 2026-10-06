from datetime import datetime, date
from sqlalchemy import String, Text, Integer, BigInteger, Float, Boolean, DateTime, ForeignKey, func, Date
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    court: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    judgment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="uploading")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(Text)
    file_size: Mapped[int] = mapped_column(BigInteger)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nlp_model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nlp_method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pages = relationship("DocumentPage", cascade="all, delete-orphan")
    entities = relationship("Entity", cascade="all, delete-orphan")
    sections = relationship("Section", cascade="all, delete-orphan")
    chunks = relationship("Chunk", cascade="all, delete-orphan")

class DocumentPage(Base):
    __tablename__ = "document_pages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64))
    is_probably_scanned: Mapped[bool] = mapped_column(Boolean, default=False)

class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page_id: Mapped[str | None] = mapped_column(ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=True)
    label: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.75)

class Section(Base):
    __tablename__ = "sections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page_id: Mapped[str | None] = mapped_column(ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=True)
    section_type: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.65)

class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page_id: Mapped[str | None] = mapped_column(ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=True)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
