"""
Integration tests driven through the real FastAPI app (TestClient), not
just the unit-level budget module. These exist specifically because a real
bug was found by hand during development: declining an over-budget item at
the *flight* stage (the first budget-checked step) incorrectly resumed the
trip at "review" instead of back at "select_flight", because the original
negotiate() endpoint inferred the resume point from which fields happened
to be set on the trip rather than tracking it explicitly. That inference
is gone; these tests pin the correct behavior at every stage so it can't
silently come back.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_trip(budget_cap=30000, destination="JAI"):
    r = client.post("/trip", json={
        "origin": "DEL", "destination": destination,
        "depart_date": "2026-12-05", "return_date": "2026-12-09",
        "travelers": 1, "budget_cap": budget_cap, "currency": "INR", "language": "en-IN",
    })
    assert r.status_code == 200
    return r.json()


def test_create_trip_rejects_same_origin_destination():
    r = client.post("/trip", json={
        "origin": "DEL", "destination": "DEL",
        "depart_date": "2026-12-05", "return_date": "2026-12-09",
        "travelers": 1, "budget_cap": 20000, "currency": "INR", "language": "en-IN",
    })
    assert r.status_code == 422


def test_create_trip_rejects_return_before_depart():
    r = client.post("/trip", json={
        "origin": "DEL", "destination": "JAI",
        "depart_date": "2026-12-09", "return_date": "2026-12-05",
        "travelers": 1, "budget_cap": 20000, "currency": "INR", "language": "en-IN",
    })
    assert r.status_code == 422


def test_flight_stage_decline_returns_to_flight_picker():
    """The bug: this used to resume at 'review'. Must resume at 'select_flight'."""
    trip = make_trip(budget_cap=2000)  # tiny cap — cheapest flight alone will exceed it
    flight_no = trip["flight_options"][0]["flight_no"]

    r = client.post(f"/trip/{trip['trip_id']}/flight", json={"flight_no": flight_no})
    body = r.json()
    assert body["status"] == "negotiate"
    assert body["running_total"] == 0  # nothing added yet

    r = client.post(f"/trip/{trip['trip_id']}/negotiate", json={"choice": "remove_item"})
    body = r.json()
    assert body["status"] == "select_flight"
    assert body["running_total"] == 0


def test_hotel_stage_decline_returns_to_hotel_picker():
    trip = make_trip(budget_cap=10000)
    flight_no = min(trip["flight_options"], key=lambda f: f["price_inr"])["flight_no"]
    r = client.post(f"/trip/{trip['trip_id']}/flight", json={"flight_no": flight_no})
    body = r.json()

    if body["status"] == "negotiate":
        pytest.skip("cap too tight for this synthetic scenario — flight alone exceeded it")

    assert body["status"] == "select_hotel"
    hotel_name = max(body["hotel_options"], key=lambda h: h["total_price_inr"])["name"]  # force overage
    r = client.post(f"/trip/{trip['trip_id']}/hotel", json={"name": hotel_name})
    body = r.json()

    if body["status"] != "negotiate":
        pytest.skip("cap too generous for this synthetic scenario to trigger a decline")

    r = client.post(f"/trip/{trip['trip_id']}/negotiate", json={"choice": "remove_item"})
    body = r.json()
    assert body["status"] == "select_hotel"


def test_approve_overage_advances_past_the_stage_that_failed():
    trip = make_trip(budget_cap=2000)
    flight_no = trip["flight_options"][0]["flight_no"]
    r = client.post(f"/trip/{trip['trip_id']}/flight", json={"flight_no": flight_no})
    assert r.json()["status"] == "negotiate"

    r = client.post(f"/trip/{trip['trip_id']}/negotiate", json={"choice": "approve_overage"})
    body = r.json()
    assert body["status"] == "select_hotel"  # advanced, not stuck or skipped ahead
    assert body["running_total"] > 0


def test_raise_cap_requires_strictly_higher_cap():
    trip = make_trip(budget_cap=2000)
    flight_no = trip["flight_options"][0]["flight_no"]
    client.post(f"/trip/{trip['trip_id']}/flight", json={"flight_no": flight_no})

    r = client.post(f"/trip/{trip['trip_id']}/negotiate", json={"choice": "raise_cap", "new_cap": 1000})
    assert r.status_code == 422


def test_confirm_blocked_while_negotiation_pending():
    trip = make_trip(budget_cap=2000)
    flight_no = trip["flight_options"][0]["flight_no"]
    client.post(f"/trip/{trip['trip_id']}/flight", json={"flight_no": flight_no})

    r = client.post(f"/trip/{trip['trip_id']}/confirm")
    assert r.status_code == 400


def test_confirmed_total_never_exceeds_final_cap():
    trip = make_trip(budget_cap=50000)
    flight_no = min(trip["flight_options"], key=lambda f: f["price_inr"])["flight_no"]
    body = client.post(f"/trip/{trip['trip_id']}/flight", json={"flight_no": flight_no}).json()
    hotel_name = min(body["hotel_options"], key=lambda h: h["total_price_inr"])["name"]
    body = client.post(f"/trip/{trip['trip_id']}/hotel", json={"name": hotel_name}).json()

    r = client.post(f"/trip/{trip['trip_id']}/package/continue")
    assert r.json()["status"] == "select_guide"

    r = client.post(f"/trip/{trip['trip_id']}/skip-guide")
    assert r.json()["status"] == "review"

    r = client.post(f"/trip/{trip['trip_id']}/confirm")
    body = r.json()
    assert body["status"] == "confirmed"
    assert body["running_total"] <= body["budget_cap"]


def test_package_continue_rejected_from_wrong_stage():
    trip = make_trip(budget_cap=50000)
    # trip is still at select_flight — continuing to guide should be rejected
    r = client.post(f"/trip/{trip['trip_id']}/package/continue")
    assert r.status_code == 400


def test_reality_check_unknown_destination_does_not_crash():
    r = client.get("/reality-check", params={
        "destination": "Nowhereville", "duration_days": 4, "budget_cap": 10000,
    })
    assert r.status_code == 200
    assert r.json()["resolved"] is False


def test_reality_check_known_destination_returns_verdict():
    r = client.get("/reality-check", params={
        "destination": "GOI", "duration_days": 4, "budget_cap": 15000,
    })
    body = r.json()
    assert body["resolved"] is True
    assert body["comparison"]["verdict"] in ("comfortable", "tight", "unrealistic")
