from unittest.mock import patch

import pytest
from starlette.requests import Request

from app.config import config
from app.controllers.base import verify_token
from app.models.exception import HttpException


def request_with_headers(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/ping",
            "headers": headers,
            "query_string": b"",
            "server": ("testserver", 80),
        }
    )


def test_verify_token_accepts_x_api_key_with_constant_time_comparison():
    request = request_with_headers([(b"x-api-key", b"correct-secret")])
    with patch.dict(config.app, {"api_key": "correct-secret"}), patch.object(
        config, "environment", "production"
    ):
        assert verify_token(request) is None


def test_verify_token_accepts_bearer_token():
    request = request_with_headers([(b"authorization", b"Bearer correct-secret")])
    with patch.dict(config.app, {"api_key": "correct-secret"}), patch.object(
        config, "environment", "production"
    ):
        assert verify_token(request) is None


@pytest.mark.parametrize(
    "headers",
    [
        [(b"x-api-key", b"wrong")],
        [(b"x-api-key", b"correct-secret"), (b"x-api-key", b"correct-secret")],
        [(b"x-api-key", b"correct-secret"), (b"authorization", b"Bearer correct-secret")],
        [(b"authorization", b"Basic correct-secret")],
    ],
)
def test_verify_token_rejects_invalid_or_ambiguous_headers(headers):
    request = request_with_headers(headers)
    with patch.dict(config.app, {"api_key": "correct-secret"}), patch.object(
        config, "environment", "production"
    ):
        with pytest.raises(HttpException) as exc_info:
            verify_token(request)
    assert exc_info.value.status_code == 401


def test_production_never_allows_empty_key():
    request = request_with_headers([])
    with patch.dict(config.app, {"api_key": ""}), patch.object(
        config, "environment", "production"
    ):
        with pytest.raises(HttpException) as exc_info:
            verify_token(request)
    assert exc_info.value.status_code == 500
