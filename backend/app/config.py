"""
All environment-driven config lives here — nowhere else in the codebase
reads os.environ directly. Drop real keys into a .env file (see .env.example)
and flip the matching USE_MOCK_* flag to false; no other file needs to change.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — fine, just export env vars manually


def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # Flights
    use_mock_flights: bool = _bool("USE_MOCK_FLIGHTS", True)
    amadeus_api_key: str = os.environ.get("AMADEUS_API_KEY", "")
    amadeus_api_secret: str = os.environ.get("AMADEUS_API_SECRET", "")

    # Hotels
    use_mock_hotels: bool = _bool("USE_MOCK_HOTELS", True)
    hotelbeds_api_key: str = os.environ.get("HOTELBEDS_API_KEY", "")
    hotelbeds_api_secret: str = os.environ.get("HOTELBEDS_API_SECRET", "")

    # CORS — tighten this for a real deployment
    cors_origins: list[str] = os.environ.get("CORS_ORIGINS", "*").split(",")


settings = Settings()
