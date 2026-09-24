"""
Waypoint backend — from-scratch hackathon build.

Flow: POST /trip (also runs the reality check) -> pick a flight -> pick a
hotel -> pick a package + swap components -> pick a guide -> confirm.
Every money-adding step routes through budget.check(); a failed check
always comes back with negotiation_options, never a flat refusal.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import budget, db, itinerary, search, trips
from .config import settings

app = FastAPI(title="Waypoint API", version="2.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Reality check — callable before a trip even exists
# ---------------------------------------------------------------------------

@app.get("/reality-check")
def reality_check(destination: str, duration_days: int, budget_cap: float, currency: str = "INR"):
    if budget_cap <= 0:
        raise HTTPException(422, "budget_cap must be > 0")
    return itinerary.compare(destination, duration_days, Decimal(str(budget_cap)), currency)


# ---------------------------------------------------------------------------
# Trip lifecycle
# ---------------------------------------------------------------------------

class CreateTripBody(BaseModel):
    origin: str
    destination: str
    depart_date: str
    return_date: str
    travelers: int = Field(1, ge=1, le=20)
    budget_cap: float = Field(..., gt=0)
    currency: str = "INR"
    language: str = "en-IN"


def _duration(depart: str, ret: str) -> int:
    from datetime import date
    d1, d2 = date.fromisoformat(depart), date.fromisoformat(ret)
    days = (d2 - d1).days
    if days <= 0:
        raise HTTPException(422, "return_date must be after depart_date")
    return days


@app.post("/trip")
def create_trip(body: CreateTripBody):
    if body.origin.strip().upper() == body.destination.strip().upper():
        raise HTTPException(422, "origin and destination can't be the same")
    try:
        duration = _duration(body.depart_date, body.return_date)
    except ValueError:
        raise HTTPException(422, "depart_date and return_date must be valid ISO dates (YYYY-MM-DD)")
    trip = trips.create(
        origin=body.origin, destination=body.destination,
        depart_date=body.depart_date, return_date=body.return_date,
        duration_days=duration, travelers=body.travelers,
        budget_cap=Decimal(str(body.budget_cap)), currency=body.currency,
        language=body.language,
    )
    trip.log("reasoning", f"Planning {duration}-day trip to {body.destination}, cap ₹{trip.budget_cap:,.0f}")
    trip.flight_options = search.search_flights(body.origin, body.destination, body.depart_date, body.travelers)
    trip.log("tool_result", f"Found {len(trip.flight_options)} flight options")
    return trip.to_dict()


def _get_trip(trip_id: str) -> trips.Trip:
    trip = trips.get(trip_id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    return trip


@app.get("/trip/{trip_id}")
def get_trip(trip_id: str):
    return _get_trip(trip_id).to_dict()


# ---------------------------------------------------------------------------
# Flight
# ---------------------------------------------------------------------------

class SelectFlightBody(BaseModel):
    flight_no: str


@app.post("/trip/{trip_id}/flight")
def select_flight(trip_id: str, body: SelectFlightBody):
    trip = _get_trip(trip_id)
    flight = next((f for f in trip.flight_options if f["flight_no"] == body.flight_no), None)
    if not flight:
        raise HTTPException(404, "Flight not in this trip's options")
    decision = trips.try_add(
        trip, Decimal(str(flight["price_inr"])), f"the {flight['airline']} flight",
        advance_to="select_hotel",
    )
    if decision.allowed:
        trip.chosen_flight = flight
        trip.hotel_options = search.search_hotels(trip.destination, trip.depart_date, trip.return_date, trip.travelers)
        trip.log("tool_result", f"Found {len(trip.hotel_options)} hotel options")
    return trip.to_dict()


# ---------------------------------------------------------------------------
# Hotel
# ---------------------------------------------------------------------------

class SelectHotelBody(BaseModel):
    name: str


@app.post("/trip/{trip_id}/hotel")
def select_hotel(trip_id: str, body: SelectHotelBody):
    trip = _get_trip(trip_id)
    hotel = next((h for h in trip.hotel_options if h["name"] == body.name), None)
    if not hotel:
        raise HTTPException(404, "Hotel not in this trip's options")
    decision = trips.try_add(
        trip, Decimal(str(hotel["total_price_inr"])), f"{hotel['name']}",
        advance_to="select_package",
    )
    if decision.allowed:
        trip.chosen_hotel = hotel
        city = db.resolve_city(trip.destination)
        if city:
            pkgs = db.packages_for_city(city["city_id"], limit=1)
            if pkgs:
                trip.package_id = pkgs[0]["package_id"]
                trip.package_components = db.package_components(trip.package_id)
                trip.log("tool_result", f"Loaded package '{pkgs[0]['name']}' with {len(trip.package_components)} components")
    return trip.to_dict()


# ---------------------------------------------------------------------------
# Package components — swap, remove/restore
# ---------------------------------------------------------------------------

@app.get("/trip/{trip_id}/package/alternatives/{component_id}")
def get_alternatives(trip_id: str, component_id: str):
    trip = _get_trip(trip_id)
    if not trip.package_id:
        raise HTTPException(400, "No package selected yet")
    return db.component_alternatives(trip.package_id, component_id)


class SwapBody(BaseModel):
    from_component_id: str
    to_component_id: str


@app.post("/trip/{trip_id}/package/swap")
def swap_component(trip_id: str, body: SwapBody):
    trip = _get_trip(trip_id)
    alts = db.component_alternatives(trip.package_id, body.from_component_id)
    target = next((a for a in alts if a["component_id"] == body.to_component_id), None)
    if not target:
        raise HTTPException(404, "Not a valid swap target")
    from_comp = next((c for c in trip.package_components if c["component_id"] == body.from_component_id), None)
    delta = db.d(target["price_delta"]) - db.d(from_comp["price_delta"] if from_comp else 0)
    decision = trips.try_add(
        trip, delta, f"swapping in {target['title']}",
        advance_to="select_package",  # a swap never advances the trip a stage, win or lose
    )
    if decision.allowed:
        trip.package_components = [
            (target | {"day_index": from_comp.get("day_index") if from_comp else None,
                       "swap_group": from_comp.get("swap_group") if from_comp else None})
            if c["component_id"] == body.from_component_id else c
            for c in trip.package_components
        ]
        trip.log("decision", f"Swapped in {target['title']} ({'+' if delta >= 0 else ''}₹{delta:,.0f})")
    return trip.to_dict()


@app.post("/trip/{trip_id}/package/continue")
def continue_from_package(trip_id: str):
    """Explicit, server-authoritative step transition — package review is
    done, move on to guide selection. Kept as a real endpoint (not a
    frontend-only state flip) so a page refresh or a later negotiation
    can't lose track of which step the trip is actually on."""
    trip = _get_trip(trip_id)
    if trip.status != "select_package":
        raise HTTPException(400, f"Can't continue from '{trip.status}'")
    trip.status = "select_guide"
    return trip.to_dict()


# ---------------------------------------------------------------------------
# Guides — now actually reachable from the frontend
# ---------------------------------------------------------------------------

@app.get("/trip/{trip_id}/guides")
def list_guides(trip_id: str, specialisation: Optional[str] = None):
    trip = _get_trip(trip_id)
    city = db.resolve_city(trip.destination)
    if not city:
        return []
    langs = [trip.language, "en-IN"]
    return db.match_guides(city["city_id"], langs, specialisation, None)


class SelectGuideBody(BaseModel):
    guide_id: str
    days: int = 1


@app.post("/trip/{trip_id}/guide")
def select_guide(trip_id: str, body: SelectGuideBody):
    trip = _get_trip(trip_id)
    if trip.status != "select_guide":
        raise HTTPException(400, f"Can't book a guide from '{trip.status}'")
    city = db.resolve_city(trip.destination)
    guides = db.match_guides(city["city_id"], None, None, None, limit=100) if city else []
    guide = next((g for g in guides if g["guide_id"] == body.guide_id), None)
    if not guide:
        raise HTTPException(404, "Guide not found for this destination")
    cost = db.d(guide["day_rate"]) * body.days
    decision = trips.try_add(
        trip, cost, f"guide {guide['display_name']} ({body.days}d)",
        advance_to="review",
    )
    if decision.allowed:
        trip.chosen_guide = {**guide, "days_booked": body.days, "total_cost": float(cost)}
        trip.log("decision", f"Booked guide {guide['display_name']} for {body.days} day(s)")
    return trip.to_dict()


@app.post("/trip/{trip_id}/skip-guide")
def skip_guide(trip_id: str):
    trip = _get_trip(trip_id)
    if trip.status != "select_guide":
        raise HTTPException(400, f"Can't skip a guide from '{trip.status}'")
    trip.status = "review"
    trip.log("decision", "Skipped guide booking")
    return trip.to_dict()


# ---------------------------------------------------------------------------
# Negotiation
# ---------------------------------------------------------------------------

class NegotiateBody(BaseModel):
    choice: budget.Choice
    new_cap: Optional[float] = None


@app.post("/trip/{trip_id}/negotiate")
def negotiate(trip_id: str, body: NegotiateBody):
    trip = _get_trip(trip_id)
    if not trip.pending:
        raise HTTPException(400, "Nothing to negotiate right now")

    amount = Decimal(trip.pending["amount"])
    label = trip.pending["label"]
    retry_status = trip.pending["retry_status"]
    advance_status = trip.pending["advance_status"]

    if body.choice == "approve_overage":
        trip.running_total += amount
        trip.status = advance_status
        trip.log("decision", f"Approved the overage for {label}")
    elif body.choice == "raise_cap":
        if not body.new_cap or Decimal(str(body.new_cap)) <= trip.budget_cap:
            raise HTTPException(422, "new_cap must be greater than the current cap")
        trip.budget_cap = Decimal(str(body.new_cap))
        trip.running_total += amount
        trip.status = advance_status
        trip.log("decision", f"Raised cap to ₹{trip.budget_cap:,.0f} and approved {label}")
    elif body.choice == "remove_item":
        trip.status = retry_status
        trip.log("decision", f"Dropped {label} — back to {retry_status.replace('_', ' ')}")
    elif body.choice == "swap_cheaper":
        trip.status = retry_status
        trip.log("decision", f"Returning to pick a cheaper alternative to {label}")

    trip.negotiation_options = []
    trip.pending = None
    return trip.to_dict()


# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------

@app.post("/trip/{trip_id}/confirm")
def confirm(trip_id: str):
    trip = _get_trip(trip_id)
    if trip.status == "negotiate":
        raise HTTPException(400, "Resolve the pending budget negotiation first")
    trip.status = "confirmed"
    trip.log("decision", f"Trip confirmed — final total ₹{trip.running_total:,.0f} of ₹{trip.budget_cap:,.0f} cap")
    return trip.to_dict()
