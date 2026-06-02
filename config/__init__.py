"""Configuration package for Enterprise Analytics Platform.

Provides:
    Settings: Centralized application settings from environment variables.
    settings: Pre-instantiated singleton Settings instance.
"""

from __future__ import annotations

from .settings import Settings, settings

__all__ = ["Settings", "settings"]
