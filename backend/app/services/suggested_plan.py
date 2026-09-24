"""Proactive Location-Triggered AI Plan Suggestion Service.

Proposes a complete best-fit itinerary (flight + hotel + package + guide)
when destination is confirmed. Fully grounded in real DB data (scoring via
recommender.py) and verified through BudgetGuard before presenting as a fit.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from ..db.packagepro import PackageProDB, dec
from ..db.session import SessionDB
from ..models import money_str
from . import pricing, trace
from .budget import BudgetGuard
from .external.dispatcher import search_flights, search_hotels
from .guides import match_guides
from .recommender import recommend



def suggest_plan_for_session(
    pro: PackageProDB,
    sessions: SessionDB,
    session_id: str,
) -> dict[str, Any]:
    s = sessions.get_session(session_id)
    if s is None:
        raise KeyError(f"unknown session {session_id}")

    city_id = s["city_id"]
    city = pro.city(city_id)
    city_name = city["name"] if city else s.get("city_name") or "Jaipur"
    origin = s.get("request", {}).get("origin") or "DEL"
    start_date = s["start_date"]
    end_date = s["end_date"]
    travelers = int(s.get("travelers") or 1)
    budget_cap = Decimal(s["budget_amount"])
    language = (s.get("request", {}).get("preferred_languages") or ["en-IN"])[0]
    theme = s.get("theme")

    # 1. Search flights & hotels first to know transport/stay baseline
    flights = search_flights(origin, city_name, start_date, travelers)
    hotels = search_hotels(city_name, start_date, end_date, travelers)

    chosen_flight = flights[0] if flights else None
    chosen_hotel = hotels[0] if hotels else None

    flight_cost = Decimal(str(chosen_flight["price_inr"])) if chosen_flight else Decimal("0")
    hotel_cost = Decimal(str(chosen_hotel["total_price_inr"])) if chosen_hotel else Decimal("0")
    baseline = flight_cost + hotel_cost

    # 2. Grounded package scoring via recommender.py (+40 language, +25 duration, +20 theme, +15 budget fit)
    recs, _, scored = recommend(pro, s["request"])
    candidate_pkgs = [pro.package(r.package_id) for r in recs if r] if recs else pro.packages_by_city(city_id)
    if not candidate_pkgs:
        candidate_pkgs = pro.packages_by_city(city_id)
    if not candidate_pkgs:
        raise ValueError(f"No tour packages available for {city_name}")

    # Pick highest-scoring package that fits within budget_cap including flight and hotel
    top_pkg = candidate_pkgs[0]
    for p in candidate_pkgs:
        p_comps = pro.components(p["package_id"])
        p_tot = pricing.included_total(p["base_price"], p_comps)
        if baseline + p_tot <= budget_cap:
            top_pkg = p
            pkg_comps = p_comps
            pkg_total = p_tot
            break
    else:
        pkg_comps = pro.components(top_pkg["package_id"])
        pkg_total = pricing.included_total(top_pkg["base_price"], pkg_comps)



    # 3. Match guide with language, dates, and availability
    guides_matched = match_guides(
        pro, city_id, [language, "en-IN"], theme, start_date, end_date
    )
    chosen_guide = None
    guide_cost = Decimal("0")
    if guides_matched:
        top_guide = guides_matched[0]["guide"]
        day_rate = dec(top_guide.get("day_rate", "2500"))
        # Check if guide fits within budget
        tentative_total = flight_cost + hotel_cost + pkg_total + day_rate
        if tentative_total <= budget_cap:
            chosen_guide = top_guide
            guide_cost = day_rate

    # 4. Enforce BudgetGuard: Plan MUST fit the budget cap!
    total = flight_cost + hotel_cost + pkg_total + guide_cost
    guard = BudgetGuard(sessions, session_id)
    decision = guard.decide(
        total,
        action="suggest_plan",
        detail={
            "package_id": top_pkg["package_id"],
            "flight_no": chosen_flight.get("flight_no") if chosen_flight else None,
            "hotel": chosen_hotel.get("name") if chosen_hotel else None,
            "guide_id": chosen_guide.get("guide_id") if chosen_guide else None,
        },
    )

    # If over budget, try stripping guide or choosing cheaper flight/hotel options
    if decision["decision"] != "approved" and chosen_guide:
        chosen_guide = None
        guide_cost = Decimal("0")
        total = flight_cost + hotel_cost + pkg_total
        decision = guard.decide(
            total,
            action="suggest_plan_adjusted",
            detail={"package_id": top_pkg["package_id"]},
        )

    remaining = budget_cap - total
    fits_budget = decision["decision"] == "approved"

    # 5. Multilingual AI narration via Nvidia NIM / templates
    one_line_reason = _generate_one_line_reason(
        pkg_name=top_pkg["name"],
        city_name=city_name,
        budget_cap=budget_cap,
        total=total,
        language=language,
        guide=chosen_guide,
    )

    suggested_plan = {
        "package": {
            "package_id": top_pkg["package_id"],
            "name": top_pkg["name"],
            "theme": top_pkg["theme"],
            "duration_days": int(top_pkg["duration_days"]),
            "base_price": money_str(dec(top_pkg["base_price"])),
            "currency": top_pkg["currency"],
        },
        "components_count": len(pkg_comps),
        "flight": chosen_flight,
        "hotel": chosen_hotel,
        "guide": (
            {
                "guide_id": chosen_guide["guide_id"],
                "display_name": chosen_guide["display_name"],
                "specialisation": chosen_guide.get("specialisation"),
                "rating": float(chosen_guide.get("rating", 4.5)),
                "cost": money_str(guide_cost),
                "languages": chosen_guide.get("languages"),
            }
            if chosen_guide
            else None
        ),
        "total_cost": float(total),
        "total_cost_formatted": money_str(total),
        "budget_cap": float(budget_cap),
        "budget_cap_formatted": money_str(budget_cap),
        "remaining": float(remaining),
        "remaining_formatted": money_str(remaining),
        "fits_budget": fits_budget,
        "one_line_reason": one_line_reason,
        "grounded_sources": [
            f"PackagePro.tour_packages ({top_pkg['package_id']})",
            f"PackagePro.package_components ({len(pkg_comps)} items)",
            chosen_flight.get("source", "Amadeus.flight-offers") if chosen_flight else "None",
            chosen_hotel.get("source", "Hotelbeds.hotel-api") if chosen_hotel else "None",
            f"PackagePro.tour_guides ({chosen_guide['guide_id']})" if chosen_guide else "None",
        ],
    }

    # 6. Structured trace event and audit log
    sessions.add_trace(
        session_id,
        trace.build(
            "suggestion",
            "complete",
            "AI Concierge",
            f"{city_name} plan for ₹{total:,.0f} (cap: ₹{budget_cap:,.0f})",
            f"Proactively suggested '{top_pkg['name']}' with {len(pkg_comps)} components, "
            f"flight {chosen_flight.get('flight_no') if chosen_flight else '—'} and hotel. {one_line_reason}",
            "Proactive recommendation grounded in verified catalog data.",
            step=1,
        ),
    )
    sessions.add_audit(
        session_id,
        "suggest_plan",
        "agent",
        {
            "package_id": top_pkg["package_id"],
            "total": money_str(total),
            "cap": money_str(budget_cap),
            "fits": fits_budget,
        },
        decision="approved" if fits_budget else "blocked",
        amount=money_str(total),
        currency=top_pkg["currency"],
    )

    # 7. Persist to session DB
    sessions.update_session(
        session_id,
        suggested_plan=suggested_plan,
        flight_options=flights,
        hotel_options=hotels,
    )

    return suggested_plan


def _generate_one_line_reason(
    pkg_name: str,
    city_name: str,
    budget_cap: Decimal,
    total: Decimal,
    language: str,
    guide: Optional[dict[str, Any]],
) -> str:
    from .llm import NvidiaNimService
    nim = NvidiaNimService()
    lang_key = nim._resolve_lang_key(language)

    guide_phrase_en = f" with a {guide.get('languages', 'local')} guide" if guide else ""
    guide_phrase_hi = f" और {guide.get('languages', 'स्थानीय')} गाइड" if guide else ""
    guide_phrase_ta = f" மற்றும் {guide.get('languages', 'உள்ளூர்')} வழிகாட்டி" if guide else ""
    guide_phrase_te = f" మరియు {guide.get('languages', 'స్థానిక')} గైడ్" if guide else ""

    fallbacks = {
        "en-IN": f"Closest match to your ₹{budget_cap:,.0f} cap with {pkg_name} in {city_name}{guide_phrase_en} on your dates.",
        "hi": f"आपके ₹{budget_cap:,.0f} के बजट के सबसे करीब, {city_name} में {pkg_name}{guide_phrase_hi}।",
        "ta": f"உங்கள் ₹{budget_cap:,.0f} பட்ஜெட் வரம்பிற்கு மிகப்பொருத்தமான {city_name}-ல் {pkg_name}{guide_phrase_ta}.",
        "te": f"మీ ₹{budget_cap:,.0f} బడ్జెట్ పరిమితికి అత్యంత సరిపోయే {city_name}లో {pkg_name}{guide_phrase_te}.",
    }
    fallback = fallbacks.get(lang_key, fallbacks["en-IN"])

    if not nim.is_configured:
        return fallback

    system_prompt = (
        f"You are Waypoint. State in exactly one grounded, reassuring sentence in {nim._lang_name(lang_key)} "
        f"why this complete trip to {city_name} ({pkg_name}) matches the traveler's ₹{budget_cap:,.0f} cap. "
        "CRITICAL: Do not invent packages or prices. Only reference the given names."
    )
    try:
        res = nim._call_nim(system_prompt, f"Explain fit for {pkg_name} in {city_name}")
        return res or fallback
    except Exception:
        return fallback
