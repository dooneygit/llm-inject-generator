import logging
from contextlib import contextmanager

import anthropic
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class LLMError(Exception):
    def __init__(self, status_code: int, detail: str, retry_after: str | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.retry_after = retry_after


@contextmanager
def translate_anthropic_errors():
    """Convert Anthropic SDK / parsing errors into LLMError. Most specific first."""
    try:
        yield
    except anthropic.APITimeoutError as e:
        raise LLMError(504, "Scenario generation timed out") from e
    except anthropic.RateLimitError as e:
        raise LLMError(
            503,
            "Scenario service is busy, try again later",
            e.response.headers.get("retry-after"),
        ) from e
    except (anthropic.OverloadedError, anthropic.ServiceUnavailableError) as e:
        raise LLMError(503, "Scenario service is busy, try again later") from e
    except (
        anthropic.BadRequestError,
        anthropic.AuthenticationError,
        anthropic.PermissionDeniedError,
        anthropic.NotFoundError,
        anthropic.UnprocessableEntityError,
        anthropic.CredentialsError,
    ) as e:
        # Our request or configuration is wrong, not the user's input.
        logger.error("LLM misconfiguration: %r", e)
        raise LLMError(500, "Scenario service is misconfigured") from e
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
        raise LLMError(502, "Upstream LLM service error") from e
    except ValidationError as e:
        raise LLMError(502, "LLM returned an invalid scenario") from e


def llm_error_handler(request: Request, exc: LLMError) -> JSONResponse:
    headers = {"Retry-After": exc.retry_after} if exc.retry_after else None
    return JSONResponse({"detail": exc.detail}, exc.status_code, headers=headers)
