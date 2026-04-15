from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Meta'ya yazacağın token. Bunu değiştirme.
VERIFY_TOKEN = "BASCA123"

# CORS - frontend hatalarını bitirir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check - tarayıcıdan girince
@app.get("/")
async def home():
    return {"status": "Basca Kafe Bot Live"}

# 1. META WEBHOOK DOĞRULAMA - GET /webhook
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ META WEBHOOK DOGRULANDI")
        return PlainTextResponse(content=challenge)
    
    return PlainTextResponse("error", status_code=403)

# 2. INSTAGRAM DM GELİNCE - POST /webhook  
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("🔥 INSTAGRAMDAN MESAJ GELDI")
    print(data)
    return {"ok": True}

# Dummy login endpoint - frontend hatasını keser
@app.post("/api/auth/login")
async def login():
    return {
        "status": "ok",
        "message": "dummy login endpoint (backend ready)"
    }
