"""
InstaAgent — Ana giriş noktası
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import create_tables
from app.routers import webhook, messages, auth, knowledge
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 InstaAgent başlatılıyor...")
    await create_tables()
    logger.info("✅ Veritabanı hazır")
    yield
    logger.info("👋 InstaAgent kapanıyor...")


app = FastAPI(
    title="InstaAgent API",
    description="Instagram AI Otomatik Yanıt Sistemi",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router,  prefix="/webhook",       tags=["Webhook"])
app.include_router(messages.router, prefix="/api/messages",  tags=["Messages"])
app.include_router(auth.router,     prefix="/api/auth",      tags=["Auth"])
app.include_router(knowledge.router,prefix="/api/knowledge", tags=["Knowledge"])


@app.get("/")
async def root():
    return {"status": "ok", "service": "InstaAgent", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
