from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from browser.policy import validate_destination


@dataclass(frozen=True)
class BrowserLaunchConfig:
    headless: bool = True
    navigation_timeout_ms: int = 15_000
    action_timeout_ms: int = 5_000
    max_read_chars: int = 12_000


@dataclass
class BrowserSession:
    context: Any
    page: Any
    allowed_domains: tuple[str, ...]


class ChromiumEngine:
    """Async Playwright boundary for isolated, short-lived Chromium contexts.

    No shell, host-path, credential-store, or download API is exposed. Each
    session receives its own non-persistent browser context.
    """

    def __init__(self, config: BrowserLaunchConfig | None = None) -> None:
        self.config = config or BrowserLaunchConfig()
        self.running = False
        self._playwright: Any = None
        self._browser: Any = None

    async def start(self) -> None:
        if self.running:
            return
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.launch(
                headless=self.config.headless,
                args=["--disable-extensions", "--disable-background-networking"],
            )
        except Exception:
            await self._playwright.stop()
            self._playwright = None
            raise
        self.running = True

    async def stop(self) -> None:
        try:
            if self._browser is not None:
                await self._browser.close()
        finally:
            self._browser = None
            if self._playwright is not None:
                await self._playwright.stop()
            self._playwright = None
            self.running = False

    async def new_context(self, allowed_domains: tuple[str, ...]) -> BrowserSession:
        if not self.running:
            await self.start()
        if self._browser is None:
            raise RuntimeError("Chromium browser failed to start")

        context = await self._browser.new_context(
            accept_downloads=False,
            service_workers="block",
            java_script_enabled=True,
        )

        async def guard_request(route: Any) -> None:
            allowed, _ = validate_destination(route.request.url, allowed_domains)
            if allowed:
                await route.continue_()
            else:
                await route.abort("blockedbyclient")

        await context.route("**/*", guard_request)
        page = await context.new_page()
        page.set_default_navigation_timeout(self.config.navigation_timeout_ms)
        page.set_default_timeout(self.config.action_timeout_ms)
        return BrowserSession(context=context, page=page, allowed_domains=allowed_domains)

    async def navigate(self, session: BrowserSession, url: str) -> str:
        allowed, reason = validate_destination(url, session.allowed_domains)
        if not allowed:
            raise ValueError(reason)
        response = await session.page.goto(url, wait_until="domcontentloaded")
        title = await session.page.title()
        status = response.status if response is not None else "no response"
        return f"HTTP {status}; title={title[:300]}; url={session.page.url[:1000]}"

    async def read(self, session: BrowserSession, selector: str | None = None) -> str:
        locator = session.page.locator(selector) if selector else session.page.locator("body")
        content = await locator.inner_text(timeout=self.config.action_timeout_ms)
        return content[: self.config.max_read_chars]

    async def action(
        self,
        session: BrowserSession,
        action: str,
        selector: str | None = None,
        value: str | None = None,
    ) -> str:
        if action == "find":
            if not value:
                raise ValueError("find requires a text query")
            locator = session.page.get_by_text(value, exact=False).first
            return (await locator.inner_text(timeout=self.config.action_timeout_ms))[: self.config.max_read_chars]

        if not selector:
            raise ValueError("a selector is required for this action")
        locator = session.page.locator(selector)

        if action == "click":
            await locator.click()
        elif action == "fill":
            if value is None:
                raise ValueError("fill requires a value")
            await locator.fill(value)
        elif action == "select":
            if value is None:
                raise ValueError("select requires a value")
            await locator.select_option(value)
        elif action == "press":
            if value is None:
                raise ValueError("press requires a key")
            await locator.press(value)
        else:
            raise ValueError("unsupported browser action")
        return "action completed"

    async def close(self, session: BrowserSession) -> None:
        await session.context.close()
