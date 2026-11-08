from pydantic import BaseModel, Field


SAFE_CAPABILITIES = {"browser.read", "browser.navigate"}
ALL_CAPABILITIES = SAFE_CAPABILITIES | {"browser.form"}


class SessionRequest(BaseModel):
    allowed_domains: tuple[str, ...] = Field(default=())
    allowed_urls: tuple[str, ...] = Field(default=())
    capabilities: tuple[str, ...] = ("browser.read", "browser.navigate")
    persistent: bool = False


class Session(BaseModel):
    session_id: str
    status: str
    allowed_domains: tuple[str, ...]
    allowed_urls: tuple[str, ...]
    capabilities: tuple[str, ...]


class NavigateRequest(BaseModel):
    session_id: str
    url: str


class ReadRequest(BaseModel):
    session_id: str
    selector: str | None = Field(default=None, max_length=1000)


class ActionRequest(BaseModel):
    session_id: str
    action: str
    selector: str | None = Field(default=None, max_length=1000)
    value: str | None = Field(default=None, max_length=4000)


class BrowserResult(BaseModel):
    status: str
    data: str = ""
    reason: str | None = None
