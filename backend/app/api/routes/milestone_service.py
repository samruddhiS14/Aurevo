"""Backward-compatible imports for the canonical milestone service module.

New code should import from ``app.services.milestone_service``.
"""
from app.services.milestone_service import *  # noqa: F401,F403
