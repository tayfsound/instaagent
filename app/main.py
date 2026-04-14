from fastapi import FastAPI, Request, Response
from app import webhook

app = FastAPI()

# BUNU META PANELİNDEKİ "Verify Token" ALANINA DA AYNEN YAZACAKSIN
VERIFY_TOKEN = "basca_2026"

@app.get("/")
async def root(request: Request):
    # Meta webhook doğrulaması
    mode = request.query_params.get('hub.mode')
    token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")
    
    # Normal sağlık kontrolü
    return {"status": "ok", "service": "InstaAgent", "version": "1.0.0"}

# Webhook router'ını dahil et
app.include_router(webhook.router, prefix="/webhook")