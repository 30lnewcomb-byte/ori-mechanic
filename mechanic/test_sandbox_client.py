import os
from unittest.mock import patch

import pytest

from .models import ExecutionRequest
from .sandbox_client import SandboxAPIAdapter, SandboxAPIError


def test_client_requires_token():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SandboxAPIError):
            SandboxAPIAdapter()


def test_client_uses_configured_api_boundary():
    with patch.dict(os.environ, {"SANDBOX_API_TOKEN": "test-token", "SANDBOX_API_URL": "http://sandbox:8080"}, clear=True):
        client = SandboxAPIAdapter()
        assert client.base_url == "http://sandbox:8080"
        assert client.token == "test-token"


def test_request_is_network_disabled():
    with patch.dict(os.environ, {"SANDBOX_API_TOKEN": "test-token"}, clear=True):
        request = ExecutionRequest(action_id="a1", command="python --version")
        assert request.timeout_seconds == 30
