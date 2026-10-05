from dataclasses import dataclass

@dataclass(frozen=True)
class BrowserLaunchConfig:
    headless: bool = True
    disable_gpu: bool = True
    disable_extensions: bool = True
    downloads_enabled: bool = False
    persistent_profile: bool = False

class ChromiumEngine:
    """Provider-neutral boundary for the isolated Chromium process.

    The engine intentionally exposes no shell, filesystem, or credential APIs.
    A Playwright/Chromium implementation can be attached behind this interface.
    """

    def __init__(self, config: BrowserLaunchConfig | None = None) -> None:
        self.config = config or BrowserLaunchConfig()
        self.running = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def new_context(self, allowed_domains: tuple[str, ...]):
        if not self.running:
            raise RuntimeError("Chromium engine is not running")
        return {"allowed_domains": allowed_domains, "persistent": self.config.persistent_profile}
