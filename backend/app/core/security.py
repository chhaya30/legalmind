import base64, hashlib, hmac, time
from fastapi import Depends, HTTPException, Request
from app.core.config import settings

def _role(key: str | None):
    if key and settings.ADMIN_API_KEY and hmac.compare_digest(key, settings.ADMIN_API_KEY): return "admin"
    if key and settings.EVALUATOR_API_KEY and hmac.compare_digest(key, settings.EVALUATOR_API_KEY): return "evaluator"
    return None

def make_session(role: str) -> str:
    payload=f"{role}:{int(time.time())}"
    sig=hmac.new(settings.AUTH_SECRET.encode(),payload.encode(),hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()

def session_role(token: str | None):
    try:
        raw=base64.urlsafe_b64decode(token.encode()).decode(); role,ts,sig=raw.split(":",2)
        payload=f"{role}:{ts}"
        if time.time()-int(ts)>settings.AUTH_SESSION_TTL_SECONDS: return None
        expected=hmac.new(settings.AUTH_SECRET.encode(),payload.encode(),hashlib.sha256).hexdigest()
        return role if hmac.compare_digest(sig,expected) and role in {"admin","evaluator"} else None
    except Exception: return None

def require_role(*roles):
    def dependency(request: Request):
        role=_role(request.headers.get("X-API-Key")) or session_role(request.cookies.get("legalmind_session"))
        if role not in roles: raise HTTPException(status_code=401, detail={"error":"unauthorized","message":"Valid administrator/evaluator authentication is required."})
        return role
    return dependency
