"""Flight & Hotel external provider dispatcher.

Dispatches to live APIs (Amadeus Flight Offers, Hotelbeds) when keys are
configured and USE_MOCK_* is False, otherwise falls back to deterministic
seeded mock generators so demo flows and tests are repeatable.
"""
from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any, Optional

from ... import config
from ...db.packagepro import dec

AIRLINES = ["IndiGo", "Air India", "Vistara", "SpiceJet", "Akasa Air"]
HOTEL_NAMES = [
    "Heritage Courtyard",
    "The Riverside Stay",
    "Blue Lotus Residency",
    "Palm Grove Boutique Resort",
    "Old Town Heritage Inn",
]


def _seed(*parts: str) -> int:
    return int(hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def _nights(check_in: str, check_out: str) -> int:
    from datetime import date
    try:
        d1 = date.fromisoformat(check_in)
        d2 = date.fromisoformat(check_out)
        return max(1, (d2 - d1).days)
    except Exception:
        return 3


def search_flights(
    origin: str,
    destination: str,
    date: str,
    travelers: int = 1,
) -> list[dict[str, Any]]:
    """Dispatch flight search to live Amadeus or deterministic mock."""
    if not config.USE_MOCK_FLIGHTS and config.AMADEUS_API_KEY and config.AMADEUS_API_SECRET:
        try:
            from .amadeus import AmadeusFlightAdapter
            adapter = AmadeusFlightAdapter(
                client_id=config.AMADEUS_API_KEY,
                client_secret=config.AMADEUS_API_SECRET,
            )
            live_results = adapter.search_flights(
                destination_city_name=destination,
                departure_date=date,
                origin_city_name=origin,
                travelers=travelers,
            )
            if live_results:
                out = []
                for f in live_results:
                    fare_dec = dec(f.get("total_fare", "3500"))
                    out.append({
                        "airline": f.get("airline", "IndiGo"),
                        "flight_no": f.get("flight_number") or f.get("flight_no") or "6E-204",
                        "origin": origin,
                        "destination": destination,
                        "date": date,
                        "depart_time": f.get("departure_time", "08:30"),
                        "duration_min": int(f.get("duration_minutes", 120)),
                        "price_inr": float(fare_dec),
                        "price_inr_formatted": f"₹{fare_dec:,.2f}",
                        "confidence": float(f.get("confidence", 0.95)),
                        "source": "Amadeus.flight-offers",
                    })
                return sorted(out, key=lambda x: x["price_inr"])
        except Exception:
            pass  # Fall back to mock

    # Deterministic mock flight generator
    base = 2800 + (_seed(origin, destination) % 5500)
    out = []
    for i, airline in enumerate(AIRLINES[:4]):
        unit_price = Decimal(base + i * 850 + (_seed(airline, date) % 400))
        total_price = unit_price * max(1, travelers)
        flight_num = f"{airline[:2].upper()}{100 + _seed(airline, origin) % 800}"
        out.append({
            "airline": airline,
            "flight_no": flight_num,
            "flight_number": flight_num,
            "origin": origin,
            "destination": destination,
            "date": date,
            "depart_time": f"{6 + i * 3:02d}:{(_seed(airline) % 4) * 15:02d}",
            "duration_min": 90 + (_seed(destination, airline) % 90),
            "price_inr": float(total_price),
            "price_inr_formatted": f"₹{total_price:,.2f}",
            "total_fare": str(total_price),
            "currency": "INR",
            "confidence": round(0.75 + (_seed(airline, destination) % 20) / 100, 2),
            "source": "Amadeus.flight-offers (deterministic mock)",
        })
    return sorted(out, key=lambda f: f["price_inr"])


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    travelers: int = 1,
) -> list[dict[str, Any]]:
    """Dispatch hotel search to live Hotelbeds or deterministic mock."""
    nights = _nights(check_in, check_out)

    if not config.USE_MOCK_HOTELS and config.HOTELBEDS_API_KEY and config.HOTELBEDS_API_SECRET:
        try:
            from .hotelbeds import HotelbedsAdapter
            # If live adapter configured, query it
            adapter = HotelbedsAdapter()
            live_hotels = adapter.get_hotel_rates(
                city_id=city,
                checkin_date=check_in,
                checkout_date=check_out,
            )
            if live_hotels:
                out = []
                for h in live_hotels:
                    cost_dec = dec(h.get("total_cost", "4500"))
                    rate_dec = cost_dec / nights if nights else cost_dec
                    out.append({
                        "name": f"{h.get('hotel_name')}, {city}",
                        "hotel_id": h.get("hotel_id", "htl_live"),
                        "rating": float(h.get("rating", 4.2)),
                        "nightly_rate_inr": float(rate_dec),
                        "nightly_rate_inr_formatted": f"₹{rate_dec:,.2f}",
                        "nights": nights,
                        "total_price_inr": float(cost_dec),
                        "total_price_inr_formatted": f"₹{cost_dec:,.2f}",
                        "total_cost": str(cost_dec),
                        "currency": "INR",
                        "source": "Hotelbeds.hotel-api",
                    })
                return sorted(out, key=lambda x: x["total_price_inr"])
        except Exception:
            pass

    # Deterministic mock hotel generator
    base = 1600 + (_seed(city) % 3200)
    out = []
    for i, name in enumerate(HOTEL_NAMES):
        rate = Decimal(base + i * 850 + (_seed(name, city) % 500))
        total = rate * nights
        rating = round(3.5 + (_seed(name, city) % 15) / 10, 1)
        full_name = f"{name}, {city}"
        out.append({
            "name": full_name,
            "hotel_id": f"htl_{_seed(name, city):x}",
            "hotel_name": full_name,
            "rating": rating,
            "nightly_rate_inr": float(rate),
            "nightly_rate_inr_formatted": f"₹{rate:,.2f}",
            "nights": nights,
            "total_price_inr": float(total),
            "total_price_inr_formatted": f"₹{total:,.2f}",
            "total_cost": str(total),
            "currency": "INR",
            "source": "Hotelbeds.hotel-api (deterministic mock)",
        })
    return sorted(out, key=lambda h: h["total_price_inr"])
