from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"}

READ_ONLY_ACTIONS = {"read", "screenshot", "find"}
INTERACTIVE_ACTIONS = {"click", "fill", "select", "press"}


def validate_destination(url: str, allowed_domains: tuple[str, ...]) -> tuple[bool, str]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, "only HTTPS destinations are permitted"
    if not host or host in BLOCKED_HOSTS:
        return False, "destination is blocked"
    if allowed_domains and host not in {d.lower() for d in allowed_domains}:
        return False, "destination is outside the domain allowlist"
    return True, ""


def validate_action(action: str, form_approved: bool = False) -> tuple[bool, str]:
    if action in READ_ONLY_ACTIONS:
        return True, ""
    if action in INTERACTIVE_ACTIONS and form_approved:
        return True, ""
    return False, "interactive browser action requires explicit capability approval"
