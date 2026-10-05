from pydantic import BaseModel, Field


class SessionRequest(BaseModel):
    allowed_domains: tuple[str, ...] = Field(default=())
    allowed_urls: tuple[str, ...] = Field(default=())
    persistent: bool = False


class Session(BaseModel):
    session_id: str
    status: str
    allowed_domains: tuple[str, ...]
    allowed_urls: tuple[str, ...]


class NavigateRequest(BaseModel):
    session_id: str
    url: str


class ActionRequest(BaseModel):
    session_id: str
    action: str
    selector: str | None = None
    value: str | None = Field(default=None, max_length=4000)


class BrowserResult(BaseModel):
    status: str
    data: str = ""
    reason: str | None = None
