"""
/webhook router
- GET  /webhook/instagram  → Meta doğrulama (ilk kurulumda)
- POST /webhook/instagram  → Yeni mesaj/yorum/story geldi
"""
import json
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
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
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
    
    print("=== INSTAGRAM RAW PAYLOAD ===")
    print(json.dumps(body, indent=2, ensure_ascii=False))
    print("=== PAYLOAD END ===")
    
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
               
