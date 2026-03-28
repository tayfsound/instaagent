"""
/api/auth router
Dashboard girişi için basit JWT auth.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta, timezone

from app.models import LoginRequest, TokenResponse
from app.config import settings

router = APIRouter()
security = HTTPBearer()

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token süresi doldu, tekrar giriş yapın")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Geçersiz token")


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if (
        req.username != settings.DASHBOARD_USERNAME
        or req.password != settings.DASHBOARD_PASSWORD
    ):
        raise HTTPException(401, "Kullanıcı adı veya şifre hatalı")

    token = create_token(req.username)
    return TokenResponse(access_token=token)
