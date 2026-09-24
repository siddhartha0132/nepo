"""
Budget-cap itinerary vs. market-average itinerary — computed from real
PackagePro package prices, never invented.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from . import db


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def compare(destination: str, duration_days: int, budget_cap: Decimal,
            currency: str = "INR") -> dict[str, Any]:
    city = db.resolve_city(destination)
    if not city:
        return {
            "resolved": False,
            "destination_input": destination,
            "message": (
                f"'{destination}' isn't in the PackagePro dataset yet, so there's "
                "no market comparison available — you can still plan the trip."
            ),
        }

    city_id, city_name = city["city_id"], city["city_name"]
    benchmark = db.market_benchmark(city_id, duration_days)

    candidates = db.packages_for_city(city_id, max(1, duration_days - 1), duration_days + 1, limit=50)
    affordable = [c for c in candidates if db.d(c["base_price"]) <= budget_cap]
    best_fit = max(affordable, key=lambda c: db.d(c["base_price"])) if affordable else None

    result: dict[str, Any] = {
        "resolved": True,
        "destination_input": destination,
        "city": {"city_id": city_id, "city_name": city_name},
        "duration_days": duration_days,
        "currency": currency,
        "budget_itinerary": {
            "budget_cap": _money(budget_cap),
            "best_fit_package": best_fit,
            "feasible": best_fit is not None,
        },
        "market_itinerary": None,
        "comparison": None,
    }

    if not benchmark:
        return result

    avg_total, min_total, max_total = benchmark["total_avg"], benchmark["total_min"], benchmark["total_max"]
    per_day = benchmark["price_per_day_avg"]

    result["market_itinerary"] = {
        "benchmark_total": _money(avg_total),
        "benchmark_total_min": _money(min_total),
        "benchmark_total_max": _money(max_total),
        "sample_size": benchmark["sample_size"],
        "fallback_level": benchmark["fallback_level"],
    }

    gap = budget_cap - avg_total
    ratio = (budget_cap / avg_total) if avg_total else Decimal(0)
    verdict = "comfortable" if ratio >= Decimal("1.15") else "tight" if ratio >= Decimal("0.85") else "unrealistic"

    span = max_total - min_total
    range_position = float(max(Decimal(0), min(Decimal(1), (budget_cap - min_total) / span))) if span > 0 else 0.5

    nearest_hundred = Decimal("1E2")
    result["comparison"] = {
        "gap_inr": _money(gap),
        "gap_pct": float((gap / avg_total * 100).quantize(Decimal("0.1"))) if avg_total else 0.0,
        "verdict": verdict,
        "range_position": round(range_position, 3),
        "data_confidence": (
            "high" if benchmark["fallback_level"] == "city" and benchmark["sample_size"] >= 3
            else "medium" if benchmark["fallback_level"] in ("city", "state") else "low"
        ),
        "recommendations": {
            "budget_needed_for_tight": (
                _money((avg_total * Decimal("0.85")).quantize(nearest_hundred, rounding=ROUND_HALF_UP))
                if verdict == "unrealistic" else None
            ),
            "budget_needed_for_comfortable": (
                _money((avg_total * Decimal("1.15")).quantize(nearest_hundred, rounding=ROUND_HALF_UP))
                if verdict != "comfortable" else None
            ),
            "max_days_at_current_budget": (
                int(budget_cap // per_day) if per_day and int(budget_cap // per_day) < duration_days else None
            ),
        },
    }
    return result
