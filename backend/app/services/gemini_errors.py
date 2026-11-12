"""Typed errors for the Gemini integration."""
class GeminiServiceError(Exception):
    """Base Gemini integration error safe to return to API clients."""

class GeminiUnavailableError(GeminiServiceError):
    """Gemini is unavailable after bounded retries."""

class GeminiInvalidResponseError(GeminiServiceError):
    """Gemini returned empty or structurally invalid content."""
