"""
Claude AI servisi
- Bilgi tabanından context hazırlar (basit RAG)
- Claude'a sistem promptu + mesaj gönderir
- Yanıt + güven skoru döner
"""
import anthropic
import asyncpg
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an Instagram customer service assistant.
Your job: reply to customer messages quickly, warmly, and helpfully.

LANGUAGE RULE (most important):
- ALWAYS reply in the SAME language the customer used.
- Examples: Turkish message → Turkish reply | English message → English reply |
  Bosanski poruka → Bosanski odgovor | Deutsche Nachricht → Deutsche Antwort |
  Arabski → Arabski | Französisch → Französisch ... and so on for ANY language.
- If you cannot detect the language, default to English.
- Never switch languages mid-reply.

OTHER RULES:
- Use a warm, friendly tone (emojis are fine, but don't overdo it)
- Only use information from the knowledge base provided
- If you don't know something, say "Our team will get back to you as soon as possible 🙏"
  (in the customer's language)
- Keep replies to 2-3 sentences max
- Never guarantee price or stock — use "approximately / estimated"

RESPONSE FORMAT (JSON only, no extra text):
{
  "response": "The reply text to send to the customer (in their language)",
  "confidence": 0.95,
  "sources": ["kb_file_used.txt"],
  "category": "stock | price | shipping | complaint | general",
  "needs_human": false,
  "detected_language": "tr | en | bs | de | fr | ar | ..."
}

Set needs_human=true if:
- Customer is angry or complaining
- Topic is payment or refund
- There is a threat or insult
- You are less than 70% confident in your answer
"""


async def generate_reply(message_content: str, db: asyncpg.Connection) -> dict:
    """
    Mesaj içeriğine göre Claude'dan yanıt üretir.
    Returns: {response, confidence, sources, category, needs_human}
    """
    # 1) Bilgi tabanını çek
    kb_rows = await db.fetch("SELECT filename, content FROM knowledge_base")
    kb_context = ""
    sources_available = []
    for row in kb_rows:
        kb_context += f"\n\n=== {row['filename']} ===\n{row['content']}"
        sources_available.append(row['filename'])

    if not kb_context:
        kb_context = "Henüz bilgi tabanı yüklenmemiş."

    # 2) Claude'a gönder
    user_prompt = f"""BİLGİ TABANI:
{kb_context}

---
MÜŞTERİ MESAJI:
"{message_content}"

---
Yukarıdaki bilgi tabanını kullanarak bu mesaja yanıt üret. Sadece JSON döndür."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = response.content[0].text.strip()

        # JSON parse
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)

        # Güvenlik kontrolleri
        result.setdefault("confidence", 0.5)
        result.setdefault("sources", [])
        result.setdefault("needs_human", False)
        result.setdefault("category", "general")

        logger.info(f"✅ AI yanıt üretildi — güven: {result['confidence']:.0%}")
        return result

    except Exception as e:
        logger.error(f"❌ Claude API hatası: {e}")
        return {
            "response": "Şu anda teknik bir sorun yaşıyoruz. Ekibimiz en kısa sürede size dönecek. 🙏",
            "confidence": 0.0,
            "sources": [],
            "category": "general",
            "needs_human": True,
        }


async def should_auto_send(confidence: float, needs_human: bool, db) -> bool:
    if needs_human:
        return False
    return True
