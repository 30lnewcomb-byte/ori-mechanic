from .browser_policy import validate_url
from .capabilities import Capability, CapabilityBroker


def test_browser_navigation_can_be_granted():
    broker = CapabilityBroker()
    broker.grant(Capability.BROWSER_NAVIGATE, domains=("github.com",))
    assert broker.allowed(Capability.BROWSER_NAVIGATE, "github.com")
    assert not broker.allowed(Capability.BROWSER_NAVIGATE, "example.com")


def test_email_send_requires_explicit_approval():
    broker = CapabilityBroker()
    broker.grant(Capability.EMAIL_SEND)
    assert not broker.allowed(Capability.EMAIL_SEND)
    broker.grant(Capability.EMAIL_SEND, approved=True)
    assert broker.allowed(Capability.EMAIL_SEND)


def test_browser_blocks_non_https_and_local_targets():
    assert not validate_url("http://example.com", ("example.com",))[0]
    assert not validate_url("https://127.0.0.1:8080", ())[0]
    assert validate_url("https://github.com", ("github.com",))[0]
