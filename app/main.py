from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS (frontend hatalarını bitirir)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def home():
    return {"status": "live"}

# Meta webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("🔥 WEBHOOK GELDİ")
    print(data)
    return {"ok": True}

# Dummy login endpoint (frontend hatasını keser)
@app.post("/api/auth/login")
async def login():
    return {
        "status": "ok",
        "message": "dummy login endpoint (backend ready)"
    }
