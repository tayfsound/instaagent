"""
Veritabanı bağlantısı (asyncpg + Supabase PostgreSQL)
"""
import asyncpg
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10,
        )
    return _pool


async def get_db():
    """FastAPI dependency — her request için connection verir"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def create_tables():
    """Uygulama başlangıcında tabloları oluşturur (yoksa)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id            SERIAL PRIMARY KEY,
                instagram_id  TEXT UNIQUE NOT NULL,       -- Meta'dan gelen mesaj ID
                sender_id     TEXT NOT NULL,              -- Gönderen kullanıcı ID
                sender_username TEXT,
                message_type  TEXT NOT NULL,              -- dm | comment | story_reply
                content       TEXT NOT NULL,              -- Gelen mesaj metni
                media_url     TEXT,                       -- Varsa medya linki

                -- AI yanıt alanları
                ai_response   TEXT,
                ai_confidence FLOAT,
                ai_sources    TEXT[],                     -- Hangi KB dosyalarından alındı

                -- Durum
                status        TEXT DEFAULT 'pending',     -- pending | approved | sent | escalated
                reviewed_by   TEXT,                       -- Onaylayan admin
                reviewed_at   TIMESTAMPTZ,
                sent_at       TIMESTAMPTZ,

                created_at    TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_messages_status
                ON messages(status);
            CREATE INDEX IF NOT EXISTS idx_messages_created
                ON messages(created_at DESC);

            -- Bilgi tabanı dosyaları
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id         SERIAL PRIMARY KEY,
                filename   TEXT NOT NULL,
                content    TEXT NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            -- Otomasyon kuralları
            CREATE TABLE IF NOT EXISTS rules (
                id          SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                category    TEXT NOT NULL,   -- stock | price | shipping | complaint | after_hours
                is_active   BOOLEAN DEFAULT TRUE,
                auto_reply  BOOLEAN DEFAULT FALSE,  -- true = insan onayı gerekmez
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            );

            -- Varsayılan kuralları ekle (yoksa)
            INSERT INTO rules (name, category, is_active, auto_reply)
            VALUES
                ('Stok Soruları',    'stock',       TRUE, FALSE),
                ('Fiyat/İndirim',    'price',       TRUE, FALSE),
                ('Kargo Takibi',     'shipping',    TRUE, FALSE),
                ('Şikayet Tespiti',  'complaint',   TRUE, FALSE),
                ('Mesai Dışı',       'after_hours', TRUE, TRUE),
                ('Uygunsuz İçerik',  'spam',        TRUE, FALSE)
            ON CONFLICT DO NOTHING;
        """)
        logger.info("✅ Tablolar hazır")
