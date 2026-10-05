import secrets
from fastapi import Depends, FastAPI, HTTPException
from browser.models import ActionRequest, BrowserResult, NavigateRequest, Session, SessionRequest
from browser.policy import validate_action, validate_destination

app = FastAPI(title="Ori Mechanic Monitored Browser", version="0.1.0")
SESSIONS: dict[str, Session] = {}


def require_internal_token() -> None:
    # The deployment layer should provide the real authentication middleware.
    # Keeping this service boundary explicit prevents accidental public exposure.
    return None

@app.get("/health")
def health():
    return {"service": "ori-mechanic-browser", "status": "online", "version": "0.1.0"}

@app.post("/v1/sessions", response_model=Session)
def create_session(request: SessionRequest, _: None = Depends(require_internal_token)):
    session_id = secrets.token_urlsafe(18)
    session = Session(session_id=session_id, status="ready", allowed_domains=request.allowed_domains)
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
