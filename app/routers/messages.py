"""
/api/messages router
Dashboard'un kullandığı tüm endpoint'ler burada.
"""
from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.models import ApproveRequest, EscalateRequest, StatsResponse
from app.services.instagram_service import send_reply
from app.routers.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ── İstatistikler ─────────────────────────────────────────────────────────────
@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    today_total = await db.fetchval(
        "SELECT COUNT(*) FROM messages WHERE created_at > NOW() - INTERVAL '24 hours'"
    )
    sent_today = await db.fetchval(
        "SELECT COUNT(*) FROM messages WHERE status='sent' AND created_at > NOW() - INTERVAL '24 hours'"
    )
    pending = await db.fetchval(
        "SELECT COUNT(*) FROM messages WHERE status='pending'"
    )
    avg_time = await db.fetchval("""
        SELECT EXTRACT(EPOCH FROM AVG(sent_at - created_at))
        FROM messages WHERE status='sent' AND sent_at IS NOT NULL
    """) or 0

    rate = (sent_today / today_total * 100) if today_total > 0 else 0

    return StatsResponse(
        total_today=today_total,
        auto_resolved_rate=round(rate, 1),
        avg_response_time_sec=round(avg_time, 1),
        pending_count=pending,
    )


# ── Bekleyen mesajlar ─────────────────────────────────────────────────────────
@router.get("/pending")
async def get_pending(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch("""
        SELECT * FROM messages
        WHERE status = 'pending'
        ORDER BY created_at DESC
        LIMIT 50
    """)
    return [dict(r) for r in rows]


# ── Tüm mesajlar (sayfalama ile) ──────────────────────────────────────────────
@router.get("/")
async def get_messages(
    page: int = 1,
    limit: int = 20,
    status: str = None,
    db: Connection = Depends(get_db),
    _=Depends(get_current_user),
):
    offset = (page - 1) * limit
    if status:
        rows = await db.fetch(
            "SELECT * FROM messages WHERE status=$1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
            status, limit, offset,
        )
    else:
        rows = await db.fetch(
            "SELECT * FROM messages ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [dict(r) for r in rows]


# ── Onayla ve gönder ──────────────────────────────────────────────────────────
@router.post("/approve")
async def approve_message(
    req: ApproveRequest,
    db: Connection = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    msg = await db.fetchrow(
        "SELECT * FROM messages WHERE id=$1 AND status='pending'", req.message_id
    )
    if not msg:
        raise HTTPException(404, "Mesaj bulunamadı veya zaten işlendi")

    final_text = req.edited_response or msg["ai_response"]

    # Instagram'a gönder
    success = await send_reply(msg["message_type"], msg["sender_id"], final_text)
    if not success:
        raise HTTPException(500, "Instagram'a gönderilemedi")

    # DB güncelle
    await db.execute("""
        UPDATE messages
        SET status='sent', ai_response=$1,
            reviewed_by=$2, reviewed_at=$3, sent_at=$3
        WHERE id=$4
    """, final_text, current_user, datetime.now(timezone.utc), req.message_id)

    logger.info(f"✅ Mesaj #{req.message_id} onaylandı ve gönderildi ({current_user})")
    return {"status": "sent"}


# ── İnsana yönlendir ──────────────────────────────────────────────────────────
@router.post("/escalate")
async def escalate_message(
    req: EscalateRequest,
    db: Connection = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    await db.execute("""
        UPDATE messages
        SET status='escalated', reviewed_by=$1, reviewed_at=$2
        WHERE id=$3
    """, current_user, datetime.now(timezone.utc), req.message_id)

    return {"status": "escalated"}


# ── Tek mesaj detayı ──────────────────────────────────────────────────────────
@router.get("/{message_id}")
async def get_message(
    message_id: int,
    db: Connection = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.fetchrow("SELECT * FROM messages WHERE id=$1", message_id)
    if not row:
        raise HTTPException(404, "Bulunamadı")
    return dict(row)
