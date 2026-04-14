import json
from fastapi import APIRouter, Request, HTTPException, Depends
...

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
