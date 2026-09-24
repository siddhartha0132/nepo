"""
In-memory trip sessions. A hackathon demo doesn't need a database for this —
it needs to be obviously correct. Swap for Redis/Postgres later; the shape
of a Trip is the contract, not where it lives.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from . import budget

_TRIPS: dict[str, "Trip"] = {}


@dataclass
class Trip:
    trip_id: str
    origin: str
    destination: str
    depart_date: str
    return_date: str
    duration_days: int
    travelers: int
    budget_cap: Decimal
    currency: str
    language: str
    status: str = "select_flight"
    running_total: Decimal = Decimal(0)
    flight_options: list[dict] = field(default_factory=list)
    hotel_options: list[dict] = field(default_factory=list)
    chosen_flight: dict | None = None
    chosen_hotel: dict | None = None
    package_id: str | None = None
    package_components: list[dict] = field(default_factory=list)
    removed_component_ids: set = field(default_factory=set)
    chosen_guide: dict | None = None
    negotiation_options: list[dict] = field(default_factory=list)
    pending: dict | None = None  # what triggered the current negotiation
    trace: list[dict] = field(default_factory=list)

    def log(self, kind: str, text: str):
        self.trace.append({"kind": kind, "text": text})

    def to_dict(self) -> dict[str, Any]:
        return {
            "trip_id": self.trip_id, "origin": self.origin, "destination": self.destination,
            "depart_date": self.depart_date, "return_date": self.return_date,
            "duration_days": self.duration_days, "travelers": self.travelers,
            "budget_cap": float(self.budget_cap), "currency": self.currency,
            "language": self.language, "status": self.status,
            "running_total": float(self.running_total),
            "remaining": float(self.budget_cap - self.running_total),
            "flight_options": self.flight_options, "hotel_options": self.hotel_options,
            "chosen_flight": self.chosen_flight, "chosen_hotel": self.chosen_hotel,
            "package_id": self.package_id, "package_components": self.package_components,
            "removed_component_ids": list(self.removed_component_ids),
            "chosen_guide": self.chosen_guide,
            "negotiation_options": self.negotiation_options,
            "trace": self.trace,
        }


def create(**kwargs) -> Trip:
    trip = Trip(trip_id=f"trp_{uuid.uuid4().hex[:10]}", **kwargs)
    _TRIPS[trip.trip_id] = trip
    return trip


def get(trip_id: str) -> Trip | None:
    return _TRIPS.get(trip_id)


def try_add(trip: Trip, amount: Decimal, item_label: str, advance_to: str) -> budget.BudgetDecision:
    """
    Route every add-to-trip through the budget guard.

    `advance_to` is the status the trip should move to if this succeeds —
    the caller states it explicitly rather than main.py or negotiate()
    inferring it afterwards from what happens to be set on the trip. The
    inferred version of this was a real bug: dropping an over-budget
    *flight* (the very first budget-checked step) resumed straight to
    "review" instead of back to "select_flight", because the old logic
    guessed the resume point from `chosen_flight`/`chosen_hotel` truthiness
    rather than tracking what the trip was actually doing when it failed.

    On failure, `trip.pending` carries both the current status (to retry
    the same step) and `advance_to` (to use if the traveler resolves the
    negotiation in a way that adds the item after all) — negotiate() then
    just reads these back instead of re-deriving them.
    """
    decision = budget.check(trip.running_total, trip.budget_cap, amount)
    if decision.allowed:
        trip.running_total = decision.running_total
        trip.negotiation_options = []
        trip.pending = None
        trip.status = advance_to
        trip.log("decision", f"Added {item_label} — running total now ₹{trip.running_total:,.0f}")
    else:
        trip.negotiation_options = budget.negotiation_options(decision, item_label)
        trip.pending = {
            "amount": str(amount),
            "label": item_label,
            "retry_status": trip.status,   # where to go back to if declined
            "advance_status": advance_to,  # where to go if approved anyway
        }
        trip.status = "negotiate"
        trip.log("decision", f"{item_label} would exceed your budget by ₹{decision.overage:,.0f}")
    return decision
