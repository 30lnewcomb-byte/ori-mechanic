from typing import Protocol
from .capabilities import Capability

class ApplicationAdapter(Protocol):
    name: str
    def has_capability(self, capability: Capability) -> bool: ...

class BrowserAdapter:
    name = "browser"
    capabilities = frozenset({Capability.BROWSER_READ, Capability.BROWSER_NAVIGATE, Capability.BROWSER_FORM})

    def has_capability(self, capability: Capability) -> bool:
        return capability in self.capabilities

class EmailAdapter:
    name = "email"
    capabilities = frozenset({Capability.EMAIL_READ, Capability.EMAIL_DRAFT, Capability.EMAIL_SEND})

    def has_capability(self, capability: Capability) -> bool:
        return capability in self.capabilities
