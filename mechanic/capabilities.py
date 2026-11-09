from dataclasses import dataclass
from enum import Enum

class Capability(str, Enum):
    BROWSER_READ = "browser.read"
    BROWSER_NAVIGATE = "browser.navigate"
    BROWSER_FORM = "browser.form"
    EMAIL_READ = "email.read"
    EMAIL_DRAFT = "email.draft"
    EMAIL_SEND = "email.send"

@dataclass(frozen=True)
class CapabilityGrant:
    capability: Capability
    approved: bool = False
    allowed_domains: tuple[str, ...] = ()

SAFE_AUTO = {Capability.BROWSER_READ, Capability.BROWSER_NAVIGATE}
APPROVAL_REQUIRED = {Capability.BROWSER_FORM, Capability.EMAIL_READ, Capability.EMAIL_DRAFT, Capability.EMAIL_SEND}
BROWSER_CAPABILITIES = {Capability.BROWSER_READ, Capability.BROWSER_NAVIGATE, Capability.BROWSER_FORM}

class CapabilityBroker:
    """Central gate for external application access; adapters never bypass it."""
    def __init__(self) -> None:
        self.grants: dict[Capability, CapabilityGrant] = {}

    def grant(self, capability: Capability, *, approved: bool = False, domains: tuple[str, ...] = ()) -> None:
        normalized_domains = tuple(d.strip().lower().rstrip(".") for d in domains)
        self.grants[capability] = CapabilityGrant(capability, approved, normalized_domains)

    def allowed(self, capability: Capability, domain: str | None = None) -> bool:
        grant = self.grants.get(capability)
        if not grant:
            return False
        if capability in APPROVAL_REQUIRED and not grant.approved:
            return False
        if capability in BROWSER_CAPABILITIES:
            if not domain or not grant.allowed_domains:
                return False
            if domain.strip().lower().rstrip(".") not in grant.allowed_domains:
                return False
        elif domain and grant.allowed_domains and domain.strip().lower().rstrip(".") not in grant.allowed_domains:
            return False
        return True
