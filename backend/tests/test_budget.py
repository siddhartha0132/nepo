from decimal import Decimal

from app import budget


def test_allows_when_under_cap():
    d = budget.check(Decimal("1000"), Decimal("5000"), Decimal("2000"))
    assert d.allowed is True
    assert d.running_total == Decimal("3000")
    assert d.remaining == Decimal("2000")
    assert d.overage is None


def test_allows_exactly_at_cap():
    """The cap is inclusive — spending exactly the cap is allowed, not blocked."""
    d = budget.check(Decimal("0"), Decimal("5000"), Decimal("5000"))
    assert d.allowed is True
    assert d.remaining == Decimal("0")


def test_blocks_over_cap():
    d = budget.check(Decimal("4000"), Decimal("5000"), Decimal("2000"))
    assert d.allowed is False
    assert d.overage == Decimal("1000")
    assert d.remaining == Decimal("-1000")


def test_negotiation_options_empty_when_allowed():
    d = budget.check(Decimal("0"), Decimal("5000"), Decimal("1000"))
    assert budget.negotiation_options(d, "test item") == []


def test_negotiation_options_offers_all_four_moves_when_blocked():
    d = budget.check(Decimal("4500"), Decimal("5000"), Decimal("1000"))
    opts = budget.negotiation_options(d, "a hotel")
    choices = {o["choice"] for o in opts}
    assert choices == {"approve_overage", "swap_cheaper", "remove_item", "raise_cap"}
    # the overage amount should be reflected in the approve_overage label
    approve = next(o for o in opts if o["choice"] == "approve_overage")
    assert "500" in approve["label"]
