import hmac
import os
import secrets
from fastapi import Depends, FastAPI, Header, HTTPException
from browser.models import ActionRequest, BrowserResult, NavigateRequest, Session, SessionRequest
from browser.policy import validate_action, validate_destination

app = FastAPI(title="Ori Mechanic Monitored Browser", version="0.2.0")
SESSIONS: dict[str, Session] = {}
API_TOKEN = os.environ.get("BROWSER_API_TOKEN", "")


def require_internal_token(authorization: str | None = Header(default=None)) -> None:
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="browser API authentication is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    if not hmac.compare_digest(authorization[7:], API_TOKEN):
        raise HTTPException(status_code=403, detail="invalid browser credential")


@app.get("/health")
def health():
    return {"service": "ori-mechanic-browser", "status": "online", "version": "0.2.0"}


@app.post("/v1/sessions", response_model=Session)
def create_session(request: SessionRequest, _: None = Depends(require_internal_token)):
    for url in request.allowed_urls:
        allowed, reason = validate_destination(url, request.allowed_domains)
        if not allowed:
            raise HTTPException(status_code=400, detail=f"invalid allowed URL: {reason}")
    session_id = secrets.token_urlsafe(18)
    session = Session(
        session_id=session_id,
        status="ready",
        allowed_domains=request.allowed_domains,
        allowed_urls=request.allowed_urls,
    )
    SESSIONS[session_id] = session
    return session


@app.post("/v1/navigate", response_model=BrowserResult)
def navigate(request: NavigateRequest, _: None = Depends(require_internal_token)):
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="unknown browser session")

    allowed, reason = validate_destination(request.url, session.allowed_domains)
    if not allowed:
        return BrowserResult(status="rejected", reason=reason)

    if session.allowed_urls and request.url.rstrip("/") not in {
        url.rstrip("/") for url in session.allowed_urls
    }:
        return BrowserResult(status="rejected", reason="URL is outside this session's exact URL allowlist")

    return BrowserResult(status="accepted", data="browser engine adapter not connected")


@app.post("/v1/actions", response_model=BrowserResult)
def action(request: ActionRequest, _: None = Depends(require_internal_token)):
    if request.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="unknown browser session")
    allowed, reason = validate_action(request.action)
    if not allowed:
        return BrowserResult(status="rejected", reason=reason)
    return BrowserResult(status="accepted", data="browser engine adapter not connected")


@app.post("/v1/close", response_model=BrowserResult)
def close(request: NavigateRequest, _: None = Depends(require_internal_token)):
    if request.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="unknown browser session")
    del SESSIONS[request.session_id]
    return BrowserResult(status="closed")
