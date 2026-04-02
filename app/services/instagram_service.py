"""
Instagram Graph API servisi
- DM yanıtı gönder
- Yorum yanıtı gönder
"""
import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0"


async def send_dm(recipient_id: str, message_text: str) -> bool:
    """DM olarak yanıt gönder"""
    url = f"{GRAPH_URL}/{settings.INSTAGRAM_PAGE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.INSTAGRAM_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            logger.info(f"✅ DM gönderildi → {recipient_id}")
            return True
        else:
            logger.error(f"❌ DM gönderilemedi: {resp.text}")
            return False


async def reply_to_comment(comment_id: str, message_text: str) -> bool:
    """Yoruma yanıt ver"""
    url = f"{GRAPH_URL}/{comment_id}/replies"
    headers = {
        "Authorization": f"Bearer {settings.INSTAGRAM_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": message_text,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            logger.info(f"✅ Yorum yanıtlandı → {comment_id}")
            return True
        else:
            logger.error(f"❌ Yorum yanıtlanamadı: {resp.text}")
            return False


async def send_reply(message_type: str, target_id: str, text: str) -> bool:
    """Mesaj tipine göre doğru API'yi çağır"""
    if message_type == "dm" or message_type == "story_reply":
        return await send_dm(target_id, text)
    elif message_type == "comment":
        return await reply_to_comment(target_id, text)
    else:
        logger.warning(f"Bilinmeyen mesaj tipi: {message_type}")
        return False
