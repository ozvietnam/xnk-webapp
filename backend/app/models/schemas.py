from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal


# ── HS Codes ────────────────────────────────────────────────

class HSCodeBase(BaseModel):
    code: str
    description_vi: str
    description_en: Optional[str] = None
    unit: Optional[str] = None
    tax_rate_normal: Optional[Decimal] = None
    tax_rate_preferential: Optional[Decimal] = None
    tax_rate_special: Optional[Decimal] = None
    notes: Optional[str] = None


class HSCodeResponse(HSCodeBase):
    id: str  # UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HSCodeSearchResult(HSCodeBase):
    id: str  # UUID
    similarity_score: Optional[float] = None

    class Config:
        from_attributes = True


class HSSearchResponse(BaseModel):
    results: List[HSCodeSearchResult]
    total: int
    query: str


# ── Chatbot ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[str] = []  # HS codes used in context
    session_id: Optional[str] = None


# ── Regulations ──────────────────────────────────────────────

class RegulationResponse(BaseModel):
    id: int
    category: Optional[str] = None
    title: str
    content_vi: Optional[str] = None
    effective_date: Optional[date] = None
    source_document: Optional[str] = None
    tags: List[str] = []


# ── History ──────────────────────────────────────────────────

class SearchHistoryItem(BaseModel):
    id: int
    query: str
    result_codes: List[str] = []
    created_at: datetime


# ── Stats ────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_hs_codes: int
    total_searches: int
    total_regulations: int
    popular_queries: List[dict] = []
