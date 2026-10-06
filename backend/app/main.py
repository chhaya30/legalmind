from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
import time
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import configure_logging, RequestIdMiddleware, request_id_ctx
from app.api.routes import router

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit=60):
        super().__init__(app); self.limit=max(1,int(limit)); self.window=60.0; self.hits=defaultdict(deque)
    async def dispatch(self, request: Request, call_next):
        key=request.client.host if request.client else "unknown"; now=time.monotonic(); q=self.hits[key]
        while q and now-q[0] >= self.window: q.popleft()
        if len(q) >= self.limit:
            return JSONResponse(status_code=429, content={"error":"rate_limited","message":"Too many requests. Please retry later.","request_id":request_id_ctx.get()})
        q.append(now); return await call_next(request)

configure_logging()
app = FastAPI(title=settings.APP_NAME, version="5.0.1", description="LegalMind Phase 5 — stabilized, evaluated, observable and deployable legal intelligence.")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware, limit=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(CORSMiddleware, allow_origins=settings.frontend_origins, allow_credentials=True, allow_methods=["GET","POST","DELETE","OPTIONS"], allow_headers=["*"])

@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"error":"http_error", "message":str(exc.detail)}
    detail["request_id"] = request_id_ctx.get()
    return JSONResponse(status_code=exc.status_code, content=detail)

@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    import logging; logging.getLogger(__name__).exception("Unhandled exception request_id=%s", request_id_ctx.get())
    return JSONResponse(status_code=500, content={"error":"internal_error", "message":"Unexpected server error.", "request_id":request_id_ctx.get()})

@app.get("/")
def root():
    return {"name":"LegalMind API", "version":"5.0.1", "phase":5, "jurisdiction":settings.JURISDICTION}

app.include_router(router, prefix=settings.API_PREFIX)
