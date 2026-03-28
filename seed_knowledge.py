"""
Bilgi tabanı dosyalarını veritabanına yükler.
Kullanım: python seed_knowledge.py
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

KB_DIR = Path(__file__).parent / "knowledge_base"


async def seed():
    db_url = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(db_url)

    # knowledge_base tablosuna unique index ekle (filename üzerine)
    await conn.execute("""
        ALTER TABLE knowledge_base
        ADD CONSTRAINT IF NOT EXISTS kb_filename_unique UNIQUE (filename)
    """)

    files = list(KB_DIR.glob("*.txt")) + list(KB_DIR.glob("*.md"))
    if not files:
        print("⚠️  knowledge_base/ klasöründe dosya bulunamadı")
        return

    for path in files:
        content = path.read_text(encoding="utf-8")
        await conn.execute("""
            INSERT INTO knowledge_base (filename, content)
            VALUES ($1, $2)
            ON CONFLICT (filename) DO UPDATE SET content=$2
        """, path.name, content)
        print(f"✅ Yüklendi: {path.name} ({len(content)} karakter)")

    await conn.close()
    print("\n🎉 Bilgi tabanı yüklendi!")


asyncio.run(seed())
