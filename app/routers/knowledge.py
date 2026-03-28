"""
/api/knowledge router
Bilgi tabanı dosyalarını yönet (ekle / güncelle / listele)
"""
from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from datetime import datetime, timezone

from app.database import get_db
from app.models import KnowledgeEntry
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_knowledge(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch("SELECT id, filename, updated_at FROM knowledge_base ORDER BY filename")
    return [dict(r) for r in rows]


@router.get("/{filename}")
async def get_knowledge(
    filename: str, db: Connection = Depends(get_db), _=Depends(get_current_user)
):
    row = await db.fetchrow("SELECT * FROM knowledge_base WHERE filename=$1", filename)
    if not row:
        raise HTTPException(404, "Dosya bulunamadı")
    return dict(row)


@router.post("/")
async def upsert_knowledge(
    entry: KnowledgeEntry,
    db: Connection = Depends(get_db),
    _=Depends(get_current_user),
):
    """Dosyayı ekle veya güncelle (upsert)"""
    await db.execute("""
        INSERT INTO knowledge_base (filename, content, updated_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (filename) DO UPDATE
            SET content=$2, updated_at=$3
    """, entry.filename, entry.content, datetime.now(timezone.utc))
    return {"status": "ok", "filename": entry.filename}


@router.delete("/{filename}")
async def delete_knowledge(
    filename: str, db: Connection = Depends(get_db), _=Depends(get_current_user)
):
    await db.execute("DELETE FROM knowledge_base WHERE filename=$1", filename)
    return {"status": "deleted"}
