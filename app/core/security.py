import hmac
from fastapi import Header, HTTPException
from app.core.config import settings


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not x_api_key or x_api_key not in settings.api_key_set():
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
    
    for k in settings.api_key_set():
        if hmac.compare_digest(x_api_key, k):
            return
    raise HTTPException(status_code=403, detail="Invalid API key")