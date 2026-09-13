import secrets
from typing import Annotated
from uuid import uuid4

from fastapi import Header, Request

from app.config import config
from app.models.exception import HttpException

MAX_TASK_ID_LENGTH = 128


def normalize_task_id(value: object) -> str:
    """Return a log-safe request ID, replacing invalid client input with a UUID."""
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_TASK_ID_LENGTH
        or not value.isprintable()
    ):
        return str(uuid4())
    return value


def get_task_id(request: Request) -> str:
    return normalize_task_id(request.headers.get("x-task-id"))


def get_api_key(request: Request) -> str | None:
    """Return the legacy X-API-Key header, if present."""
    value = request.headers.get("x-api-key")
    return value if isinstance(value, str) else None


def _header_values(request: Request, name: str) -> list[str]:
    """Return every value for a header, preserving duplicates for safe rejection."""
    get_list = getattr(request.headers, "getlist", None)
    if callable(get_list):
        return [value for value in get_list(name) if isinstance(value, str)]
    value = request.headers.get(name)
    return [value] if isinstance(value, str) else []


def get_api_key_values(request: Request) -> list[str]:
    """Extract exactly one API key from X-API-Key or Bearer Authorization.

    Multiple values, or sending both header forms, are intentionally preserved and
    rejected by ``verify_token`` instead of relying on proxy/client header ordering.
    """
    values = _header_values(request, "x-api-key")
    authorization_values = _header_values(request, "authorization")
    for authorization in authorization_values:
        scheme, separator, credentials = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not credentials.strip():
            values.append("")
        else:
            values.append(credentials.strip())
    return values


def verify_token(
    request: Request,
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
):
    """Verify the configured API key using constant-time comparison.

    An empty key is allowed only for the explicit development mode. Production
    startup fails in ``app.config`` when no key is configured, so accidentally
    exposing the API without authentication is prevented at the deployment layer.
    """
    configured_key = config.app.get("api_key", "")
    if not isinstance(configured_key, str):
        raise HttpException(
            task_id=get_task_id(request),
            status_code=500,
            message="API authentication is misconfigured",
        )
    if not configured_key:
        if getattr(config, "environment", "development") == "production":
            raise HttpException(
                task_id=get_task_id(request),
                status_code=500,
                message="API authentication is misconfigured",
            )
        return None

    token_values = get_api_key_values(request)
    # Keep compatibility with lightweight Request substitutes used by callers/tests.
    if not token_values and isinstance(x_api_key, str):
        token_values = [x_api_key]

    if len(token_values) != 1:
        raise HttpException(
            task_id=get_task_id(request),
            status_code=401,
            message="invalid API key",
        )

    token = token_values[0]
    if not token or not secrets.compare_digest(
        token.encode("utf-8"), configured_key.encode("utf-8")
    ):
        raise HttpException(
            task_id=get_task_id(request),
            status_code=401,
            message="invalid API key",
        )

    return None
