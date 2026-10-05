from ipaddress import ip_address
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}
BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "169.254.169.254", "metadata.google.internal",
}
BLOCKED_PORTS = {80, 21, 22, 23, 25, 110, 143, 445, 3389}

READ_ONLY_ACTIONS = {"read", "screenshot", "find"}
INTERACTIVE_ACTIONS = {"click", "fill", "select", "press"}


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


def _host_allowed(host: str, allowed_domains: tuple[str, ...]) -> bool:
    normalized = {d.lower().rstrip(".") for d in allowed_domains}
    return host in normalized


def validate_destination(url: str, allowed_domains: tuple[str, ...] = ()) -> tuple[bool, str]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return False, "only HTTPS destinations are permitted"
    if parsed.username or parsed.password:
        return False, "credentials in URLs are not permitted"
    if not host or host in BLOCKED_HOSTS:
        return False, "destination is blocked"
    if _is_private_or_reserved_host(host):
        return False, "private, loopback, link-local, reserved, or multicast destinations are blocked"
    if parsed.port and parsed.port in BLOCKED_PORTS:
        return False, "destination port is blocked"
    if allowed_domains and not _host_allowed(host, allowed_domains):
        return False, "destination is outside the domain allowlist"
    return True, ""


def validate_action(action: str, form_approved: bool = False) -> tuple[bool, str]:
    if action in READ_ONLY_ACTIONS:
        return True, ""
    if action in INTERACTIVE_ACTIONS and form_approved:
        return True, ""
    return False, "interactive browser action requires explicit capability approval"
