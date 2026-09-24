"""Reality check service — market benchmark vs traveler budget cap.

Compares user's budget against actual PackagePro tour packages and
market-average daily rates, flagging fallback level and data confidence.
Never invents data or prices.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from ..db.packagepro import PackageProDB, dec
from ..models import money_str


def _money(value: Decimal) -> str:
    return money_str(value)


def compare_budget_to_market(
    pro: PackageProDB,
    destination: str,
    duration_days: int,
    budget_cap: Decimal,
    currency: str = "INR",
    language: str = "en-IN",
) -> dict[str, Any]:
    city = pro.resolve_city(destination)
    if not city:
        return {
            "resolved": False,
            "destination_input": destination,
            "message": (
                f"'{destination}' isn't in the PackagePro dataset yet, so there's "
                "no market comparison available — you can still plan the trip."
            ),
            "data_confidence": "none",
        }

    city_id, city_name = city["city_id"], city["name"]
    duration_days = max(1, duration_days)
    benchmark = pro.market_benchmark(city_id, duration_days)

    candidates = pro.packages_for_city(city_id, min_days=max(1, duration_days - 1), max_days=duration_days + 1, limit=50)
    if not candidates:
        candidates = pro.packages_for_city(city_id, limit=50)

    affordable = [c for c in candidates if dec(c["base_price"]) <= budget_cap]
    best_fit = max(affordable, key=lambda c: dec(c["base_price"])) if affordable else None

    result: dict[str, Any] = {
        "resolved": True,
        "destination_input": destination,
        "city": {
            "city_id": city_id,
            "city_name": city_name,
            "state": city.get("state"),
            "country_code": city.get("country_code", "IN"),
        },
        "duration_days": duration_days,
        "currency": currency,
        "budget_itinerary": {
            "budget_cap": float(budget_cap),
            "budget_cap_formatted": _money(budget_cap),
            "best_fit_package": best_fit,
            "feasible": best_fit is not None,
        },
        "market_itinerary": None,
        "comparison": None,
        "data_confidence": "low",
        "ai_explanation": None,
    }

    if not benchmark:
        return result

    avg_total = benchmark["total_avg"]
    min_total = benchmark["total_min"]
    max_total = benchmark["total_max"]
    per_day = benchmark["price_per_day_avg"]

    result["market_itinerary"] = {
        "benchmark_total": float(avg_total),
        "benchmark_total_formatted": _money(avg_total),
        "benchmark_total_min": float(min_total),
        "benchmark_total_min_formatted": _money(min_total),
        "benchmark_total_max": float(max_total),
        "benchmark_total_max_formatted": _money(max_total),
        "sample_size": benchmark["sample_size"],
        "fallback_level": benchmark["fallback_level"],
    }

    gap = budget_cap - avg_total
    ratio = (budget_cap / avg_total) if avg_total > 0 else Decimal("0")
    if ratio >= Decimal("1.15"):
        verdict = "comfortable"
    elif ratio >= Decimal("0.85"):
        verdict = "tight"
    else:
        verdict = "unrealistic"

    span = max_total - min_total
    range_pos = float(max(Decimal(0), min(Decimal(1), (budget_cap - min_total) / span))) if span > 0 else 0.5

    data_confidence = (
        "high" if benchmark["fallback_level"] == "city" and benchmark["sample_size"] >= 3
        else "medium" if benchmark["fallback_level"] in ("city", "state") else "low"
    )
    result["data_confidence"] = data_confidence

    nearest_hundred = Decimal("100")
    tight_needed = (avg_total * Decimal("0.85")).quantize(nearest_hundred, rounding=ROUND_HALF_UP)
    comf_needed = (avg_total * Decimal("1.15")).quantize(nearest_hundred, rounding=ROUND_HALF_UP)
    max_days = int(budget_cap // per_day) if per_day and int(budget_cap // per_day) < duration_days else None

    result["comparison"] = {
        "gap_inr": float(gap),
        "gap_inr_formatted": _money(gap),
        "gap_pct": float(round(float((gap / avg_total * Decimal(100)) if avg_total else 0), 1)),
        "verdict": verdict,
        "range_position": round(range_pos, 3),
        "data_confidence": data_confidence,
        "recommendations": {
            "budget_needed_for_tight": float(tight_needed) if verdict == "unrealistic" else None,
            "budget_needed_for_tight_formatted": _money(tight_needed) if verdict == "unrealistic" else None,
            "budget_needed_for_comfortable": float(comf_needed) if verdict != "comfortable" else None,
            "budget_needed_for_comfortable_formatted": _money(comf_needed) if verdict != "comfortable" else None,
            "max_days_at_current_budget": max_days,
        },
    }

    # Multilingual AI explanation
    try:
        from .llm import NvidiaNimService
        nim = NvidiaNimService()
        lang_key = nim._resolve_lang_key(language)
        explanations = {
            "en-IN": {
                "comfortable": f"Your budget of ₹{budget_cap:,.0f} comfortably exceeds the ₹{avg_total:,.0f} market average for {duration_days} days in {city_name}.",
                "tight": f"Your budget of ₹{budget_cap:,.0f} is tight but feasible compared to the ₹{avg_total:,.0f} market benchmark for {city_name}.",
                "unrealistic": f"Your budget of ₹{budget_cap:,.0f} is below the typical ₹{avg_total:,.0f} market benchmark for a {duration_days}-day trip to {city_name}.",
            },
            "hi": {
                "comfortable": f"आपका ₹{budget_cap:,.0f} का बजट {city_name} में {duration_days} दिनों के लिए बाजार औसत ₹{avg_total:,.0f} से काफी बेहतर है।",
                "tight": f"आपका ₹{budget_cap:,.0f} का बजट {city_name} के लिए संभव है, हालांकि यह बाजार औसत ₹{avg_total:,.0f} के करीब है।",
                "unrealistic": f"आपका ₹{budget_cap:,.0f} का बजट {city_name} में {duration_days} दिनों के सामान्य खर्च ₹{avg_total:,.0f} से कम है।",
            },
            "ta": {
                "comfortable": f"உங்கள் ₹{budget_cap:,.0f} பட்ஜெட் {city_name}-ல் {duration_days} நாட்களுக்கான சந்தை சராசரி ₹{avg_total:,.0f}-ஐ விட போதுமானது.",
                "tight": f"உங்கள் ₹{budget_cap:,.0f} பட்ஜெட் {city_name}-ல் சாத்தியமானது, ஆனால் சந்தை சராசரிக்கு அருகில் உள்ளது.",
                "unrealistic": f"உங்கள் ₹{budget_cap:,.0f} பட்ஜெட் {city_name}-ல் {duration_days} நாட்களுக்கு வழக்கமான செலவை விட குறைவாக உள்ளது.",
            },
            "te": {
                "comfortable": f"మీ ₹{budget_cap:,.0f} బడ్జెట్ {city_name}లో {duration_days} రోజులకు మార్కెట్ సగటు ₹{avg_total:,.0f} కంటే సౌకర్యవంతంగా ఉంది.",
                "tight": f"మీ ₹{budget_cap:,.0f} బడ్జెట్ {city_name}లో సరిపోతుంది, కానీ మార్కెట్ సగటుకు దగ్గరగా ఉంది.",
                "unrealistic": f"మీ ₹{budget_cap:,.0f} బడ్జెట్ {city_name}లో {duration_days} రోజుల సాధారణ ఖర్చు కంటే తక్కువగా ఉంది.",
            },
        }
        result["ai_explanation"] = explanations.get(lang_key, explanations["en-IN"]).get(verdict)
    except Exception:
        result["ai_explanation"] = None

    return result
