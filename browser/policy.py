import re
from ipaddress import ip_address
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}
BLOCKED_PORTS = {80, 21, 22, 23, 25, 110, 143, 445, 3389}
READ_ONLY_ACTIONS = {"find"}
INTERACTIVE_ACTIONS = {"click", "fill", "select", "press"}
_DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_domain(domain: str) -> str:
    value = domain.strip().lower().rstrip(".")
    if not value or len(value) > 253 or any(not _DOMAIN_LABEL.fullmatch(label) for label in value.split(".")):
        raise ValueError("allowlist entries must be plain DNS hostnames")
    try:
        ip_address(value)
    except ValueError:
        if all(character in "0123456789." for character in value):
            raise ValueError("IP addresses cannot be used as browser allowlist entries")
        return value
    raise ValueError("IP addresses cannot be used as browser allowlist entries")


def _is_private_or_reserved_host(host: str) -> bool:
    try:
        address = ip_address(host)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def validate_destination(url: str, allowed_domains: tuple[str, ...] = ()) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        return False, "malformed destination URL"

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return False, "only HTTPS destinations are permitted"
    if parsed.username or parsed.password:
        return False, "credentials in URLs are not permitted"
    if not host or host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        return False, "destination is blocked"
    if _is_private_or_reserved_host(host):
        return False, "private, loopback, link-local, reserved, or multicast destinations are blocked"
    if port not in (None, 443) or port in BLOCKED_PORTS:
        return False, "only the standard HTTPS port is permitted"
    try:
        normalized = tuple(normalize_domain(domain) for domain in allowed_domains)
    except ValueError:
        return False, "invalid domain allowlist"
    if not normalized:
        return False, "a non-empty domain allowlist is required"
    if host not in normalized:
        return False, "destination is outside the exact domain allowlist"
    return True, ""


def validate_action(action: str, form_approved: bool = False) -> tuple[bool, str]:
    if action in READ_ONLY_ACTIONS:
        return True, ""
    if action in INTERACTIVE_ACTIONS and form_approved:
        return True, ""
    return False, "interactive browser action requires explicit form capability approval"
