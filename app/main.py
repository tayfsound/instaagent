from fastapi import FastAPI, Request, Response

app = FastAPI()

VERIFY_TOKEN = "basca_2026"

@app.get("/")
async def verify_webhook(request: Request):
    mode = request.query_params.get('hub.mode')
    token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    
    return {"status": "ok"}

@app.post("/")
async def handle_message():
    return {"status": "received"}