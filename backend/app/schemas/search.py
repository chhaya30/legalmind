from datetime import date
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class SearchMode(str, Enum):
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    mode: SearchMode = SearchMode.hybrid
    court: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    rerank: bool = True
    top_k: int = Field(default=10, ge=1, le=50)

class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    page_id: str
    section_id: Optional[str]
    case_title: str
    court: Optional[str]
    category: Optional[str]
    page_number: int
    section_type: Optional[str]
    snippet: str
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: Optional[float] = None

class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    reranked: bool
    results: list[SearchResult]
    candidate_count: int
    latency_ms: int
