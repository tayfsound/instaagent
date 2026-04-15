from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# Meta'ya yazacağın token. BUNU DEĞİŞTİRME.
VERIFY_TOKEN = "BASCA123"

# CORS - frontend hatalarını keser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. HEALTH CHECK - Tarayıcıdan girince
@app.get("/")
async def home():
    return {"status": "Basca Kafe Bot Live", "version": "2.0"}

# 2. META WEBHOOK DOĞRULAMA - GET /webhook
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ META WEBHOOK DOGRULANDI")
        return PlainTextResponse(content=challenge)
    
    print("❌ DOGRULAMA HATASI: Token uyusmadi")
    return PlainTextResponse("error", status_code=403)

# 3. WEBHOOK VERİ ALICI - POST /webhook
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("🔥 WEBHOOK GELDI:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    try:
        for entry in data.get("entry", []):
            # A. INSTAGRAM DM MESAJI
            if "messaging" in entry:
                for messaging_event in entry["messaging"]:
                    if "message" in messaging_event:
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"].get("text", "")
                        print(f"📩 DM ALGILANDI: {sender_id} -> {message_text}")
                        # n8n'e gidecek veri:
                        # {"tip": "dm", "gonderen_id": sender_id, "mesaj": message_text}
            
            # B. INSTAGRAM YORUM GELDİ
            if "changes" in entry:
                for change in entry["changes"]:
                    if change.get("field") == "comments":
                        comment_data = change["value"]
                        comment_id = comment_data["id"]
                        comment_text = comment_data["text"]
                        from_username = comment_data["from"]["username"]
                        media_id = comment_data["media"]["id"]
                        print(f"💬 YORUM ALGILANDI: {from_username} -> {comment_text}")
                        # n8n'e gidecek veri:
                        # {"tip": "yorum", "yorum_id": comment_id, "mesaj": comment_text, "kullanici": from_username}
    
    except Exception as e:
        print(f"WEBHOOK PARSE HATASI: {e}")
    
    return {"ok": True}

# 4. DUMMY LOGIN - Frontend hatasını keser
@app.post("/api/auth/login")
async def login():
    return {
        "status": "ok",
        "message": "dummy login endpoint"
    }
