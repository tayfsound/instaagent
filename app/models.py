"""
Pydantic modelleri — API request/response şemaları
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Gelen webhook payload ─────────────────────────────────────────────────────
class WebhookMessage(BaseModel):
    object: str
    entry: list


# ── Veritabanı mesaj modeli ───────────────────────────────────────────────────
class Message(BaseModel):
    id: int
    instagram_id: str
    sender_id: str
    sender_username: Optional[str]
    message_type: str           # dm | comment | story_reply
    content: str
    media_url: Optional[str]
    ai_response: Optional[str]
    ai_confidence: Optional[float]
    ai_sources: Optional[List[str]]
    status: str                 # pending | approved | sent | escalated
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime


# ── Dashboard aksiyonları ─────────────────────────────────────────────────────
class ApproveRequest(BaseModel):
    message_id: int
    edited_response: Optional[str] = None   # Admin düzenlediyse


class EscalateRequest(BaseModel):
    message_id: int
    note: Optional[str] = None


# ── Bilgi tabanı ──────────────────────────────────────────────────────────────
class KnowledgeEntry(BaseModel):
    filename: str
    content: str


# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── İstatistikler ─────────────────────────────────────────────────────────────
class StatsResponse(BaseModel):
    total_today: int
    auto_resolved_rate: float
    avg_response_time_sec: float
    pending_count: int
