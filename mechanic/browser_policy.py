from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"}


def validate_url(url: str, allowed_domains: tuple[str, ...]) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, "only HTTPS browser navigation is allowed"
    host = (parsed.hostname or "").lower()
    if not host or host in BLOCKED_HOSTS:
        return False, "blocked browser destination"
    if allowed_domains and host not in {d.lower() for d in allowed_domains}:
        return False, "domain is not allowlisted"
    return True, ""


def redact_sensitive_text(text: str) -> str:
    # Browser output should not become a credential exfiltration channel.
    lowered = text.lower()
    sensitive_markers = ("password", "secret", "api_key", "access_token", "refresh_token", "private key")
    if any(marker in lowered for marker in sensitive_markers):
        return "[sensitive browser content withheld]"
    return text
