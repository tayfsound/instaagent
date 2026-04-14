"""
/webhook router
- GET  /webhook/instagram  → Meta doğrulama (ilk kurulumda)
- POST /webhook/instagram  → Yeni mesaj/yorum/story geldi
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from asyncpg import Connection
import logging
from datetime import datetime, timezone

from app.database import get_db
from app.config import settings
from app.services.ai_service import generate_reply, should_auto_send
from app.services.instagram_service import send_reply

router = APIRouter()
logger = logging.getLogger(__name__)

# ── 1) Meta webhook doğrulama (GET) ──────────────────────────────────────────
@router.get("/instagram")
async def verify_webhook(request: Request):
    params = request.query_params
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.INSTAGRAM_VERIFY_TOKEN:
        logger.info("✅ Webhook doğrulandı")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        logger.warning("❌ Webhook doğrulama başarısız")
        raise HTTPException(status_code=403, detail="Forbidden")

# ── 2) Yeni olay geldi (POST) ─────────────────────────────────────────────────
@router.post("/instagram")
async def receive_event(request: Request, db: Connection = Depends(get_db)):
    body = await request.json()
    logger.info(f"📩 Webhook alındı: {body.get('object')}")

    if body.get("object") != "instagram":
        return {"status": "ignored"}

    for entry in body.get("entry", []):
        # ── DM mesajları ──────────────────────────────────────────────────────
        for messaging in entry.get("messaging", []):
            msg = messaging.get("message")
            if not msg or msg.get("is_echo"):
                continue

            await _process_message(
                db=db,
                instagram_id=msg.get("mid", ""),
                sender_id=messaging["sender"]["id"],
                sender_username=None,
                message_type="dm",
                content=msg.get("text", ""),
                target_id=messaging["sender"]["id"],
            )

        # ── Yorumlar ─────────────────────────────────────────────────────────
        for change in entry.get("changes", []):
            val = change.get("value", {})
            if change.get("field") == "comments" and val.get("text"):
                await _process_message(
                    db=db,
                    instagram_id=val.get("id", ""),
                    sender_id=val.get("from", {}).get("id", ""),
                    sender_username=val.get("from", {}).get("username"),
                    message_type="comment",
                    content=val.get("text", ""),
                    target_id=val.get("id", ""),
                )

    return {"status": "ok"}

# ── Ortak işlem fonksiyonu ────────────────────────────────────────────────────
async def _process_message(
    db, instagram_id, sender_id, sender_username,
    message_type, content, target_id
):
    if not content.strip():
        return

    exists = await db.fetchval(
        "SELECT id FROM messages WHERE instagram_id = $1", instagram_id
    )
    if exists:
        return

    logger.info(f"🔍 İşleniyor [{message_type}]: {content[:60]}")

    ai_result = await generate_reply(content, db)

    auto_send = await should_auto_send(
        ai_result["confidence"], ai_result["needs_human"], db
    )

    status = "sent" if auto_send else "pending"
    sent_at = datetime.now(timezone.utc) if auto_send else None

    row_id = await db.fetchval("""
        INSERT INTO messages
            (instagram_id, sender_id, sender_username, message_type,
             content, ai_response, ai_confidence, ai_sources, status, sent_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        RETURNING id
    """,
        instagram_id, sender_id, sender_username, message_type,
        content,
        ai_result["response"], ai_result["confidence"], ai_result["sources"],
        status, sent_at,
    )

    if auto_send:
        success = await send_reply(message_type, target_id, ai_result["response"])
        if not success:
            await db.execute(
                "UPDATE messages SET status='pending', sent_at=NULL WHERE id=$1", row_id
            )
        logger.info(f"⚡ Otomatik gönderildi — mesaj #{row_id}")
    else:
        logger.info(f"⏳ İnsan onayı bekleniyor
