"""State-resumption regression tests.

These pin the bug ported from newnew: when a BudgetGuard check fails
(decision=blocked), the session MUST remain at its pre-action state.
A subsequent valid action must succeed cleanly from that exact state,
not from an incorrectly mutated intermediate state.

Rules pinned here:
1. Over-budget package select does NOT persist selected_package_id.
2. Over-budget guide select does NOT persist selected_guide_id.
3. Over-budget flight select does NOT persist selected_flight.
4. Over-budget hotel select does NOT persist selected_hotel.
5. After any blocked action, the total_amount in the DB equals the
   pre-action value (no partial writes).
6. After raising the budget cap via negotiate(), re-trying the same
   action succeeds and persists correctly.
7. negotiate(approve_overage) on a blocked action still leaves entity
   un-selected (the *guard* approves but the caller must re-select).
"""
from __future__ import annotations

import pytest

from tests.conftest import JODHPUR, JODHPUR_PACKAGE

TINY_BUDGET = {"amount": "100.00", "currency": "INR"}


def _plan_with_budget(solver, budget):
    req = dict(JODHPUR)
    req["budget"] = budget
    return solver.plan(req)["session_id"]


def _s(solver, sid):
    return solver.sessions.get_session(sid)


# ---------------------------------------------------------------------------
# 1. Package select blocked
# ---------------------------------------------------------------------------

class TestBlockedPackageSelect:
    def test_blocked_leaves_no_package_selected(self, solver):
        sid = _plan_with_budget(solver, TINY_BUDGET)
        result = solver.select_package(sid, JODHPUR_PACKAGE)
        assert result["budget"]["decision"] == "blocked"
        assert _s(solver, sid)["selected_package_id"] is None

    def test_total_amount_unchanged_after_blocked_select(self, solver):
        sid = _plan_with_budget(solver, TINY_BUDGET)
        assert _s(solver, sid)["total_amount"] is None
        solver.select_package(sid, JODHPUR_PACKAGE)
        assert _s(solver, sid)["total_amount"] is None

    def test_after_raise_cap_select_package_succeeds(self, solver):
        sid = _plan_with_budget(solver, TINY_BUDGET)
        blocked = solver.select_package(sid, JODHPUR_PACKAGE)
        assert blocked["budget"]["decision"] == "blocked"
        solver.negotiate(sid, "raise_budget_cap", "25000.00")
        ok = solver.select_package(sid, JODHPUR_PACKAGE)
        assert ok["budget"]["decision"] == "approved"
        assert _s(solver, sid)["selected_package_id"] == JODHPUR_PACKAGE

    def test_blocked_decision_is_logged_to_audit(self, solver):
        sid = _plan_with_budget(solver, TINY_BUDGET)
        solver.select_package(sid, JODHPUR_PACKAGE)
        audit = solver.sessions.audit(sid)
        assert any(
            e["action"].startswith("budget:") and e["decision"] == "blocked"
            for e in audit
        ), "A blocked select_package must produce a blocked audit entry"


# ---------------------------------------------------------------------------
# 2. Guide select blocked
# ---------------------------------------------------------------------------

class TestBlockedGuideSelect:
    @pytest.fixture
    def session_at_cap(self, solver):
        sid = _plan_with_budget(solver, {"amount": "20000.00", "currency": "INR"})
        solver.select_package(sid, JODHPUR_PACKAGE)
        # Shrink cap to exactly the package total — no room for a guide
        pkg_total = _s(solver, sid)["total_amount"]
        solver.sessions.update_session(sid, budget_amount=pkg_total)
        return sid

    def test_blocked_guide_leaves_guide_id_none(self, solver, session_at_cap):
        result = solver.select_guide(session_at_cap, "gid_460ad60c", "full_day")
        assert result["budget"]["decision"] == "blocked"
        assert _s(solver, session_at_cap)["selected_guide_id"] is None

    def test_blocked_guide_does_not_change_total_amount(self, solver, session_at_cap):
        pre = _s(solver, session_at_cap)["total_amount"]
        solver.select_guide(session_at_cap, "gid_460ad60c", "full_day")
        assert _s(solver, session_at_cap)["total_amount"] == pre

    def test_after_raise_cap_guide_select_succeeds(self, solver, session_at_cap):
        solver.select_guide(session_at_cap, "gid_460ad60c", "full_day")  # blocked
        solver.negotiate(session_at_cap, "raise_budget_cap", "30000.00")
        ok = solver.select_guide(session_at_cap, "gid_460ad60c", "full_day")
        assert ok["budget"]["decision"] == "approved"
        assert _s(solver, session_at_cap)["selected_guide_id"] == "gid_460ad60c"


# ---------------------------------------------------------------------------
# 3. Flight select blocked
# ---------------------------------------------------------------------------

EXPENSIVE_FLIGHT = {
    "flight_id": "FL999",
    "airline": "IndiGo",
    "flight_number": "6E-999",
    "origin_airport": "DEL",
    "destination_airport": "JDH",
    "total_fare": "99999.00",
    "currency": "INR",
    "source": "mock",
}


class TestBlockedFlightSelect:
    @pytest.fixture
    def session_with_package(self, solver):
        sid = _plan_with_budget(solver, {"amount": "20000.00", "currency": "INR"})
        solver.select_package(sid, JODHPUR_PACKAGE)
        return sid

    def test_blocked_flight_leaves_selected_flight_none(self, solver, session_with_package):
        result = solver.select_flight(session_with_package, EXPENSIVE_FLIGHT)
        assert result["budget"]["decision"] == "blocked"
        assert _s(solver, session_with_package)["selected_flight"] is None

    def test_blocked_flight_does_not_update_total(self, solver, session_with_package):
        pre = _s(solver, session_with_package)["total_amount"]
        solver.select_flight(session_with_package, EXPENSIVE_FLIGHT)
        assert _s(solver, session_with_package)["total_amount"] == pre


# ---------------------------------------------------------------------------
# 4. Hotel select blocked
# ---------------------------------------------------------------------------

EXPENSIVE_HOTEL = {
    "hotel_id": "HTL999",
    "hotel_name": "Grand Palace",
    "room_name": "Presidential Suite",
    "nights": 3,
    "total_cost": "99999.00",
    "currency": "INR",
    "source": "mock",
}


class TestBlockedHotelSelect:
    @pytest.fixture
    def session_with_package(self, solver):
        sid = _plan_with_budget(solver, {"amount": "20000.00", "currency": "INR"})
        solver.select_package(sid, JODHPUR_PACKAGE)
        return sid

    def test_blocked_hotel_leaves_selected_hotel_none(self, solver, session_with_package):
        result = solver.select_hotel(session_with_package, EXPENSIVE_HOTEL)
        assert result["budget"]["decision"] == "blocked"
        assert _s(solver, session_with_package)["selected_hotel"] is None

    def test_blocked_hotel_does_not_update_total(self, solver, session_with_package):
        pre = _s(solver, session_with_package)["total_amount"]
        solver.select_hotel(session_with_package, EXPENSIVE_HOTEL)
        assert _s(solver, session_with_package)["total_amount"] == pre


# ---------------------------------------------------------------------------
# 5. Full round-trip: block → negotiate → resume → confirm
# ---------------------------------------------------------------------------

class TestFullResumeAfterBlock:
    def test_approve_overage_does_not_implicitly_select_package(self, solver):
        """approve_overage OKs the total but must NOT auto-select the package."""
        sid = _plan_with_budget(solver, TINY_BUDGET)
        solver.select_package(sid, JODHPUR_PACKAGE)  # blocked
        solver.negotiate(sid, "approve_overage")
        # Frontend must re-submit select_package explicitly
        assert _s(solver, sid)["selected_package_id"] is None

    def test_full_raise_cap_then_confirm(self, solver):
        """raise_budget_cap → select_package → trust_receipt → confirm."""
        sid = _plan_with_budget(solver, TINY_BUDGET)
        solver.select_package(sid, JODHPUR_PACKAGE)  # blocked
        assert _s(solver, sid)["selected_package_id"] is None

        solver.negotiate(sid, "raise_budget_cap", "25000.00")
        solver.select_package(sid, JODHPUR_PACKAGE)  # now approved
        assert _s(solver, sid)["selected_package_id"] == JODHPUR_PACKAGE

        receipt = solver.trust_receipt(sid)
        assert receipt["budget_guard"] == "Passed"
        conf = solver.confirm(sid)
        assert conf["confirmation"]["status"] == "mock_confirmed"

    def test_multiple_blocks_do_not_accumulate_total(self, solver):
        """Calling select_package multiple times while blocked must not increment total."""
        sid = _plan_with_budget(solver, TINY_BUDGET)
        for _ in range(3):
            result = solver.select_package(sid, JODHPUR_PACKAGE)
            assert result["budget"]["decision"] == "blocked"
        # total_amount must still be None (no partial accumulation)
        assert _s(solver, sid)["total_amount"] is None
