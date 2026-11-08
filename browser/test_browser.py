import pytest

from browser.policy import normalize_domain, validate_action, validate_destination


def test_https_allowlisted_destination_is_accepted():
    assert validate_destination("https://github.com/openai", ("github.com",))[0]


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com",
        "https://127.0.0.1",
        "https://[::1]",
        "https://localhost",
        "https://service.local",
        "https://metadata.google.internal",
        "https://github.com:8443",
        "https://user:pass@github.com",
    ],
)
def test_unsafe_destinations_are_rejected(url):
    assert not validate_destination(url, ("github.com",))[0]


def test_domain_matching_is_exact_not_suffix_based():
    assert not validate_destination("https://github.com.attacker.example", ("github.com",))[0]
    assert not validate_destination("https://sub.github.com", ("github.com",))[0]


def test_empty_allowlist_fails_closed():
    assert not validate_destination("https://example.com", ())[0]


def test_domain_normalization_and_validation():
    assert normalize_domain(" GitHub.com. ") == "github.com"
    with pytest.raises(ValueError):
        normalize_domain("https://github.com")
    with pytest.raises(ValueError):
        normalize_domain("127.0.0.1")


def test_form_actions_require_explicit_capability():
    assert validate_action("click", form_approved=False)[0] is False
    assert validate_action("click", form_approved=True)[0] is True
    assert validate_action("find", form_approved=False)[0] is True
    assert validate_action("exec", form_approved=True)[0] is False
