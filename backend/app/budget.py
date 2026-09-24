"""
The one rule the whole product is built around: nothing is ever added to a
trip if it would push the running total over the traveler's cap — and when
that happens, the traveler gets four concrete moves, never a flat refusal.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Choice = Literal["approve_overage", "swap_cheaper", "remove_item", "raise_cap"]


@dataclass
class BudgetDecision:
    allowed: bool
    running_total: Decimal
    cap: Decimal
    remaining: Decimal
    pct_used: float
    overage: Decimal | None = None

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "running_total": float(self.running_total),
            "cap": float(self.cap),
            "remaining": float(self.remaining),
            "pct_used": self.pct_used,
            "overage": float(self.overage) if self.overage is not None else None,
        }


def check(running_total: Decimal, cap: Decimal, add: Decimal = Decimal(0)) -> BudgetDecision:
    """Would `running_total + add` still fit under `cap`? The only function
    in the codebase allowed to make that call — every add-to-trip action
    routes through here, never decides for itself."""
    new_total = running_total + add
    remaining = cap - new_total
    allowed = remaining >= 0
    return BudgetDecision(
        allowed=allowed,
        running_total=new_total,
        cap=cap,
        remaining=remaining,
        pct_used=float((new_total / cap * 100)) if cap else 0.0,
        overage=(-remaining) if not allowed else None,
    )


def negotiation_options(decision: BudgetDecision, item_label: str) -> list[dict]:
    """Four honest moves, not a wall — returned as structured data (choice,
    item_label, amount) rather than a pre-built English sentence, so the
    frontend can render this in whatever language the traveler is using.
    A `label` field is still included as an English fallback for any
    client that doesn't localize."""
    if decision.allowed:
        return []
    overage = decision.overage or Decimal(0)
    return [
        {
            "choice": "approve_overage",
            "item_label": item_label,
            "amount": float(overage),
            "label": f"Approve the extra ₹{overage:,.0f} for {item_label}",
        },
        {
            "choice": "swap_cheaper",
            "item_label": item_label,
            "amount": None,
            "label": f"Swap {item_label} for a cheaper alternative",
        },
        {
            "choice": "remove_item",
            "item_label": item_label,
            "amount": None,
            "label": f"Drop {item_label} and keep the rest",
        },
        {
            "choice": "raise_cap",
            "item_label": None,
            "amount": None,
            "label": "Raise my overall trip budget",
        },
    ]
