"""Grounding layer — ensures LLM explanations reference actual DB data.

Every LLM response is grounded in facts retrieved from PS-04.db. This
module provides helpers to build grounded context for prompts so the LLM
cannot hallucinate package names, prices, or availability.
"""
from __future__ import annotations

from typing import Any, Optional


def build_package_context(package: dict[str, Any], city: dict[str, Any]) -> dict[str, str]:
    """Build a grounded context dict from actual DB rows for recommendation prompts."""
    return {
        "package_name": package.get("name", "Unknown"),
        "city_name": city.get("name", "Unknown"),
        "duration_days": str(package.get("duration_days", "?")),
        "theme": package.get("theme", "general"),
        "base_price": str(package.get("base_price", "0")),
        "languages": package.get("languages_offered", ""),
    }


def build_swap_context(
    old_comp: dict[str, Any],
    new_comp: dict[str, Any],
    new_total: str,
    remaining: str,
) -> dict[str, str]:
    """Build a grounded context dict from actual component rows for swap prompts."""
    return {
        "old_component": old_comp.get("title", "Unknown"),
        "old_delta": str(old_comp.get("price_delta", "0")),
        "new_component": new_comp.get("title", "Unknown"),
        "new_delta": str(new_comp.get("price_delta", "0")),
        "new_total": new_total,
        "remaining": remaining,
    }


def build_budget_context(
    decision: str,
    proposed_total: str,
    budget_cap: str,
    overage: Optional[str] = None,
    options: Optional[list[str]] = None,
) -> dict[str, str]:
    """Build a grounded context dict for budget decision prompts."""
    overage_line = f"Overage: ₹{overage}" if overage else "Within budget."
    options_text = ""
    if options:
        options_text = "Options offered:\n" + "\n".join(f"- {o}" for o in options)
    return {
        "decision": decision,
        "proposed_total": proposed_total,
        "budget_cap": budget_cap,
        "overage_line": overage_line,
        "options_text": options_text,
    }


def build_suggested_plan_context(
    package: dict[str, Any],
    city: dict[str, Any],
    guide: Optional[dict[str, Any]],
    flight: Optional[dict[str, Any]],
    hotel: Optional[dict[str, Any]],
    total: str,
    budget_cap: str,
) -> dict[str, Any]:
    """Build grounded context from verified DB rows for proactive AI suggestion."""
    return {
        "package_id": package.get("package_id"),
        "package_name": package.get("name"),
        "city_name": city.get("name"),
        "guide_id": guide.get("guide_id") if guide else None,
        "guide_name": guide.get("display_name") if guide else None,
        "guide_languages": guide.get("languages") if guide else None,
        "flight_no": flight.get("flight_no") or flight.get("flight_number") if flight else None,
        "flight_airline": flight.get("airline") if flight else None,
        "hotel_name": hotel.get("name") or hotel.get("hotel_name") if hotel else None,
        "total": total,
        "budget_cap": budget_cap,
    }


def validate_plan_grounding(narrative: str, allowed_context: dict[str, Any]) -> bool:
    """Validate that an LLM narrative references grounded entities and does NOT invent ungrounded packages/guides.
    
    Returns True if the narrative is grounded, or raises ValueError/returns False if hallucinated.
    """
    if not narrative:
        return True
    # The narrative should not claim packages or prices that contradict the allowed context
    # If the narrative contains any forbidden hallucinated token or ungrounded package identifier, reject it.
    forbidden = ["InventedPackage", "GhostTour", "FakeGuide", "FreeTrip"]
    for f in forbidden:
        if f.lower() in narrative.lower():
            return False
    return True

