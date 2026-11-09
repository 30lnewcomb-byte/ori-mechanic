import pytest

from .browser_policy import validate_url
from .capabilities import Capability, CapabilityBroker


@pytest.mark.parametrize(
    "capability",
    [Capability.BROWSER_READ, Capability.BROWSER_NAVIGATE, Capability.BROWSER_FORM],
)
def test_browser_capabilities_require_an_exact_domain_allowlist(capability):
    broker = CapabilityBroker()
    broker.grant(capability, approved=True, domains=("github.com",))
    assert broker.allowed(capability, "github.com")
    assert broker.allowed(capability, "github.com.")
    assert not broker.allowed(capability, "sub.github.com")
    assert not broker.allowed(capability, "github.com.attacker.example")
    assert not broker.allowed(capability)


@pytest.mark.parametrize(
    "capability",
    [Capability.BROWSER_READ, Capability.BROWSER_NAVIGATE, Capability.BROWSER_FORM],
)
def test_browser_capabilities_fail_closed_without_a_domain_allowlist(capability):
    broker = CapabilityBroker()
    broker.grant(capability, approved=True)
    assert not broker.allowed(capability, "github.com")
    assert not broker.allowed(capability)


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


def test_browser_url_policy_fails_closed_for_empty_or_non_exact_allowlists():
    assert not validate_url("https://example.com", ())[0]
    assert not validate_url("https://sub.github.com", ("github.com",))[0]
    assert not validate_url("https://github.com.attacker.example", ("github.com",))[0]
