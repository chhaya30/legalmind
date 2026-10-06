from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class EntityOut(BaseModel):
    id: str
    label: str
    text: str
    page_number: Optional[int] = None
    confidence: float

class SectionOut(BaseModel):
    id: str
    section_type: str
    text: str
    page_number: Optional[int] = None
    confidence: float

class PageOut(BaseModel):
    id: str
    page_number: int
    text: str
    checksum: str
    is_probably_scanned: bool

class DocumentSummary(BaseModel):
    id: str
    filename: str
    title: Optional[str]
    court: Optional[str]
    case_number: Optional[str]
    category: Optional[str]
    category_confidence: Optional[float]
    judgment_date: Optional[date] = None
    status: str
    error_message: Optional[str]
    page_count: Optional[int]
    file_size: int
    created_at: Optional[datetime] = None

class DocumentOut(DocumentSummary):
    entities: List[EntityOut] = Field(default_factory=list)
    sections: List[SectionOut] = Field(default_factory=list)

class UploadAccepted(BaseModel):
    id: str
    status: str
    message: str
