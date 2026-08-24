"""Offline, payload-blind CCM reference adapter for Cyrisk."""

from .adapter import adapt
from .models import AdapterRequest, AdapterResult

__all__ = ["AdapterRequest", "AdapterResult", "adapt"]
