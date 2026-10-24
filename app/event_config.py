"""Event metadata for passes and certificates (from environment)."""

from __future__ import annotations

import os


def event_name() -> str:
    return os.getenv("EVENT_NAME", "EventPilot Demo Event").strip() or "EventPilot Demo Event"


def event_date() -> str:
    return os.getenv("EVENT_DATE", "TBD").strip() or "TBD"


def event_venue() -> str:
    return os.getenv("EVENT_VENUE", "TBD").strip() or "TBD"
