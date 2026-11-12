
"""Bounded, timeout-protected Gemini client wrapper."""

import json
import logging
import time

import httpx
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.gemini_errors import (
    GeminiInvalidResponseError,
    GeminiUnavailableError,
)

logger = logging.getLogger(__name__)


class GeminiService:
    """Provides safe text and JSON generation through the Gemini API."""

    RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

    def __init__(self):
        api_key = settings.GEMINI_API_KEY

        if not api_key or not api_key.strip():
            raise GeminiUnavailableError(
                "Gemini API key is not configured."
            )

        timeout_ms = max(
            1000,
            int(settings.GEMINI_TIMEOUT_SECONDS * 1000),
        )

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )

        self.model = settings.GEMINI_MODEL

    @staticmethod
    def _get_status_code(exc: Exception):
        """Extract the HTTP status from Gemini or HTTPX exceptions."""

        status_code = getattr(exc, "code", None)

        if status_code is None:
            status_code = getattr(exc, "status_code", None)

        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)

        try:
            return int(status_code) if status_code is not None else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _is_retryable(cls, exc: Exception, status_code):
        """Retry only temporary API or network failures."""

        if status_code in cls.RETRYABLE_STATUS_CODES:
            return True

        if isinstance(
            exc,
            (
                httpx.TimeoutException,
                httpx.NetworkError,
                TimeoutError,
                ConnectionError,
            ),
        ):
            return True

        return False

    def _generate(self, prompt: str, json_response: bool = False) -> str:
        attempts = max(1, min(settings.GEMINI_MAX_ATTEMPTS, 4))

        if json_response:
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        else:
            config = types.GenerateContentConfig()

        for attempt in range(attempts):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )

                if not response.text or not response.text.strip():
                    raise GeminiInvalidResponseError(
                        "AI returned an empty response."
                    )

                return response.text.strip()

            except GeminiInvalidResponseError:
                raise

            except Exception as exc:
                status_code = self._get_status_code(exc)

                retryable = self._is_retryable(
                    exc,
                    status_code,
                )

                logger.warning(
                    "Gemini request failed "
                    "(attempt %s/%s, error=%s, status=%s)",
                    attempt + 1,
                    attempts,
                    type(exc).__name__,
                    status_code,
                )

                if not retryable:
                    raise GeminiUnavailableError(
                        "Gemini request failed. Please check the "
                        "API configuration and try again."
                    ) from exc

                if attempt < attempts - 1:
                    delay = min(1.0 * (2 ** attempt), 4.0)

                    logger.info(
                        "Retrying Gemini request after %s seconds.",
                        delay,
                    )

                    time.sleep(delay)
                else:
                    raise GeminiUnavailableError(
                        "Gemini is temporarily unavailable or the "
                        "request exceeded its deadline. Please retry later."
                    ) from exc

        raise GeminiUnavailableError(
            "Gemini is temporarily unavailable. Please retry later."
        )

    def generate_json(self, prompt: str) -> dict:
        """Generate and parse a JSON response."""

        response_text = self._generate(
            prompt,
            json_response=True,
        )

        try:
            result = json.loads(response_text)

        except json.JSONDecodeError as exc:
            raise GeminiInvalidResponseError(
                "AI returned invalid JSON. Please retry."
            ) from exc

        if not isinstance(result, dict):
            raise GeminiInvalidResponseError(
                "AI returned an unexpected structured response."
            )

        return result

    def generate_text(self, prompt: str) -> str:
        """Generate a plain text response."""

        return self._generate(
            prompt,
            json_response=False,
        )
