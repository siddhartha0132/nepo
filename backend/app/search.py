"""
Flight & hotel search — one dispatcher per resource, each choosing between
the mock generator and a real provider based on app.config.settings.

To go live: implement the body of real_amadeus_flights() /
real_hotelbeds_hotels() below (both already have the exact return shape
documented), drop your keys into .env, and set USE_MOCK_FLIGHTS=false /
USE_MOCK_HOTELS=false. Nothing outside this file needs to change — every
caller in main.py only ever calls search_flights()/search_hotels().
"""
from __future__ import annotations

import hashlib
from decimal import Decimal

from .config import settings

# ---------------------------------------------------------------------------
# Public dispatchers — the only functions the rest of the app calls
# ---------------------------------------------------------------------------

def search_flights(origin: str, destination: str, date: str, travelers: int = 1) -> list[dict]:
    if settings.use_mock_flights:
        return _mock_flights(origin, destination, date, travelers)
    return real_amadeus_flights(origin, destination, date, travelers)


def search_hotels(city: str, check_in: str, check_out: str, travelers: int = 1) -> list[dict]:
    if settings.use_mock_hotels:
        return _mock_hotels(city, check_in, check_out, travelers)
    return real_hotelbeds_hotels(city, check_in, check_out, travelers)


# ---------------------------------------------------------------------------
# Real providers — implement these when API keys are ready
# ---------------------------------------------------------------------------

def real_amadeus_flights(origin: str, destination: str, date: str, travelers: int) -> list[dict]:
    """
    Wire up the Amadeus Flight Offers Search API here using
    settings.amadeus_api_key / settings.amadeus_api_secret.

    Must return a list of dicts shaped exactly like _mock_flights()'s
    output — trips.py and main.py read `price_inr` and `flight_no` off
    each item and don't care about anything else in the dict, but keeping
    the same keys (airline, origin, destination, date, depart_time,
    duration_min, price_inr, confidence) means the frontend needs zero
    changes when this goes live.
    """
    raise NotImplementedError(
        "Real flight search not wired up yet — implement real_amadeus_flights() "
        "in search.py, or set USE_MOCK_FLIGHTS=true in .env to keep using mock data."
    )


def real_hotelbeds_hotels(city: str, check_in: str, check_out: str, travelers: int) -> list[dict]:
    """
    Wire up the Hotelbeds Booking API here using settings.hotelbeds_api_key /
    settings.hotelbeds_api_secret. Must return a list shaped like
    _mock_hotels()'s output (name, rating, nightly_rate_inr, nights,
    total_price_inr) for the same reason as above.
    """
    raise NotImplementedError(
        "Real hotel search not wired up yet — implement real_hotelbeds_hotels() "
        "in search.py, or set USE_MOCK_HOTELS=true in .env to keep using mock data."
    )


# ---------------------------------------------------------------------------
# Mock providers — deterministic (seeded off the route), so a demo is
# repeatable and the dual-itinerary comparison stays consistent within a
# session without needing to cache anything.
# ---------------------------------------------------------------------------

def _seed(*parts: str) -> int:
    return int(hashlib.sha1("|".join(parts).encode()).hexdigest()[:8], 16)


AIRLINES = ["IndiGo", "Air India", "Vistara", "SpiceJet", "Akasa Air"]


def _mock_flights(origin: str, destination: str, date: str, travelers: int = 1) -> list[dict]:
    base = 2800 + (_seed(origin, destination) % 6000)
    out = []
    for i, airline in enumerate(AIRLINES[:4]):
        price = Decimal(base + i * 850 + (_seed(airline, date) % 400))
        out.append({
            "airline": airline,
            "flight_no": f"{airline[:2].upper()}{100 + _seed(airline, origin) % 800}",
            "origin": origin,
            "destination": destination,
            "date": date,
            "depart_time": f"{6 + i * 3:02d}:{(_seed(airline) % 4) * 15:02d}",
            "duration_min": 90 + (_seed(destination, airline) % 90),
            "price_inr": float(price * travelers),
            "confidence": round(0.7 + (_seed(airline, destination) % 25) / 100, 2),
        })
    return sorted(out, key=lambda f: f["price_inr"])


HOTEL_NAMES = ["Heritage Courtyard", "The Riverside", "Blue Lotus Stay",
               "Palm Grove Resort", "Old Town Inn"]


def _mock_hotels(city: str, check_in: str, check_out: str, travelers: int = 1) -> list[dict]:
    nights = max(1, _nights(check_in, check_out))
    base = 1600 + (_seed(city) % 3500)
    out = []
    for i, name in enumerate(HOTEL_NAMES):
        rate = Decimal(base + i * 900 + (_seed(name, city) % 500))
        out.append({
            "name": f"{name}, {city}",
            "rating": round(3.4 + (_seed(name, city) % 16) / 10, 1),
            "nightly_rate_inr": float(rate),
            "nights": nights,
            "total_price_inr": float(rate * nights),
        })
    return sorted(out, key=lambda h: h["total_price_inr"])


def _nights(check_in: str, check_out: str) -> int:
    from datetime import date
    try:
        d1 = date.fromisoformat(check_in)
        d2 = date.fromisoformat(check_out)
        return max(1, (d2 - d1).days)
    except Exception:
        return 3
