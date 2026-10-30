import hmac
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException

from browser.engine import BrowserSession, ChromiumEngine
from browser.models import (
    ALL_CAPABILITIES,
    ActionRequest,
    BrowserResult,
    NavigateRequest,
    ReadRequest,
    Session,
    SessionRequest,
)
from browser.monitor import BrowserMonitor
from browser.policy import normalize_domain, validate_action, validate_destination

engine = ChromiumEngine()
monitor = BrowserMonitor()
SESSIONS: dict[str, Session] = {}
ENGINE_SESSIONS: dict[str, BrowserSession] = {}
API_TOKEN = os.environ.get("BROWSER_API_TOKEN", "")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    for browser_session in list(ENGINE_SESSIONS.values()):
        try:
            engine.close(browser_session)
        except Exception:
            pass
    ENGINE_SESSIONS.clear()
    SESSIONS.clear()
    engine.stop()


app = FastAPI(title="Ori Mechanic Monitored Browser", version="0.3.0", lifespan=lifespan)


def require_internal_token(authorization: str | None = Header(default=None)) -> None:
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="browser API authentication is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    if not hmac.compare_digest(authorization[7:], API_TOKEN):
        raise HTTPException(status_code=403, detail="invalid browser credential")


def get_session(session_id: str) -> tuple[Session, BrowserSession]:
    record = SESSIONS.get(session_id)
    live = ENGINE_SESSIONS.get(session_id)
    if record is None or live is None:
        raise HTTPException(status_code=404, detail="unknown browser session")
    return record, live


@app.get("/health")
def health():
    return {
        "service": "ori-mechanic-browser",
        "status": "ready" if engine.running else "idle",
        "engine": "chromium" if engine.running else "not_started",
        "version": "0.3.0",
    }


@app.post("/v1/sessions", response_model=Session)
def create_session(request: SessionRequest, _: None = Depends(require_internal_token)):
    if request.persistent:
        raise HTTPException(status_code=400, detail="persistent browser profiles are not supported")
    if not request.allowed_domains:
        raise HTTPException(status_code=400, detail="at least one allowed domain is required")
    try:
        domains = tuple(dict.fromkeys(normalize_domain(domain) for domain in request.allowed_domains))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not request.capabilities or not set(request.capabilities).issubset(ALL_CAPABILITIES):
        raise HTTPException(status_code=400, detail="unknown or empty browser capability set")
    if len(set(request.capabilities)) != len(request.capabilities):
        raise HTTPException(status_code=400, detail="duplicate browser capabilities are not permitted")
    for url in request.allowed_urls:
        allowed, reason = validate_destination(url, domains)
        if not allowed:
            raise HTTPException(status_code=400, detail=f"invalid allowed URL: {reason}")

    try:
        live_session = engine.new_context(domains)
    except Exception as exc:
        monitor.record("engine_start_failed", type(exc).__name__)
        raise HTTPException(status_code=503, detail="isolated Chromium engine could not start") from exc

    session_id = secrets.token_urlsafe(18)
    session = Session(
        session_id=session_id,
        status="ready",
        allowed_domains=domains,
        allowed_urls=request.allowed_urls,
        capabilities=request.capabilities,
    )
    SESSIONS[session_id] = session
    ENGINE_SESSIONS[session_id] = live_session
    monitor.record("session_created", session_id)
    return session


@app.post("/v1/navigate", response_model=BrowserResult)
def navigate(request: NavigateRequest, _: None = Depends(require_internal_token)):
    record, live = get_session(request.session_id)
    if "browser.navigate" not in record.capabilities:
        raise HTTPException(status_code=403, detail="browser navigation capability was not granted")
    allowed, reason = validate_destination(request.url, record.allowed_domains)
    if not allowed:
        monitor.record("navigation_rejected", reason)
        return BrowserResult(status="rejected", reason=reason)
    if record.allowed_urls and request.url.rstrip("/") not in {url.rstrip("/") for url in record.allowed_urls}:
        monitor.record("navigation_rejected", "exact URL allowlist")
        return BrowserResult(status="rejected", reason="URL is outside this session's exact URL allowlist")
    try:
        result = engine.navigate(live, request.url)
    except Exception as exc:
        monitor.record("navigation_failed", type(exc).__name__)
        return BrowserResult(status="failed", reason="navigation failed; see browser service logs")
    monitor.record("navigation_completed", request.url.split("/", 3)[2])
    return BrowserResult(status="completed", data=result)


@app.post("/v1/read", response_model=BrowserResult)
def read_page(request: ReadRequest, _: None = Depends(require_internal_token)):
    record, live = get_session(request.session_id)
    if "browser.read" not in record.capabilities:
        raise HTTPException(status_code=403, detail="browser read capability was not granted")
    try:
        content = engine.read(live, request.selector)
    except Exception as exc:
        monitor.record("read_failed", type(exc).__name__)
        return BrowserResult(status="failed", reason="page content could not be read")
    monitor.record("page_read", request.session_id)
    return BrowserResult(status="completed", data=content)


@app.post("/v1/actions", response_model=BrowserResult)
def action(request: ActionRequest, _: None = Depends(require_internal_token)):
    record, live = get_session(request.session_id)
    form_approved = "browser.form" in record.capabilities
    allowed, reason = validate_action(request.action, form_approved=form_approved)
    if not allowed:
        monitor.record("action_rejected", request.action)
        return BrowserResult(status="rejected", reason=reason)
    if request.action == "find" and "browser.read" not in record.capabilities:
        raise HTTPException(status_code=403, detail="browser read capability was not granted")
    try:
        result = engine.action(live, request.action, request.selector, request.value)
    except Exception as exc:
        monitor.record("action_failed", f"{request.action}:{type(exc).__name__}")
        return BrowserResult(status="failed", reason="browser action failed; see browser service logs")
    monitor.record("action_completed", request.action)
    return BrowserResult(status="completed", data=result)


@app.post("/v1/close", response_model=BrowserResult)
def close(request: NavigateRequest, _: None = Depends(require_internal_token)):
    _, live = get_session(request.session_id)
    try:
        engine.close(live)
    finally:
        ENGINE_SESSIONS.pop(request.session_id, None)
        SESSIONS.pop(request.session_id, None)
    monitor.record("session_closed", request.session_id)
    return BrowserResult(status="closed")
