"""
Read-only access to the real PackagePro dataset (PS-04.db).

Money convention: every price column in this DB is stored as TEXT and is
treated as Decimal from the moment it leaves SQLite — never float. A price
is only converted to a plain number at the API boundary (see money() in
schemas.py), for exactly the reason a bank statement doesn't do its running
total in binary floating point.
"""
from __future__ import annotations

import sqlite3
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "PS-04.db"

_conn: sqlite3.Connection | None = None


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Dataset not found at {DB_PATH}")
        _conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return [dict(r) for r in conn().execute(sql, params).fetchall()]


def row(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    r = conn().execute(sql, params).fetchone()
    return dict(r) if r else None


def d(value: Any) -> Decimal:
    """String/int/float -> Decimal, the only safe way to bring DB money in."""
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Cities — the seam between free-text/IATA input and the real dataset
# ---------------------------------------------------------------------------

IATA_TO_CITY = {
    "DEL": "New Delhi", "BOM": "Mumbai", "BLR": "Bengaluru", "MAA": "Chennai",
    "CCU": "Kolkata", "HYD": "Hyderabad", "PNQ": "Pune", "COK": "Kochi",
    "GOI": "Panaji", "GOX": "Panaji", "JAI": "Jaipur", "UDR": "Udaipur",
    "JDH": "Jodhpur", "ATQ": "Amritsar", "AGR": "Agra", "VNS": "Varanasi",
    "LKO": "Lucknow", "IXL": "Leh", "SXR": "Srinagar", "IXM": "Madurai",
    "TIR": "Tirupati", "VTZ": "Visakhapatnam", "BBI": "Bhubaneswar",
    "GAU": "Guwahati", "KTM": "Kathmandu", "CMB": "Colombo", "DPS": "Bali",
    "BKK": "Bangkok", "DXB": "Dubai", "AUH": "Abu Dhabi", "DOH": "Doha",
    "SIN": "Singapore", "KUL": "Kuala Lumpur", "ZRH": "Zurich",
}
CITY_ALIASES = {
    "GOA": "Panaji", "BANGALORE": "Bengaluru", "MYSORE": "Mysuru",
    "TRIVANDRUM": "Thiruvananthapuram", "COCHIN": "Kochi", "BOMBAY": "Mumbai",
    "CALCUTTA": "Kolkata", "MADRAS": "Chennai", "DELHI": "New Delhi",
    "VIZAG": "Visakhapatnam",
}


@lru_cache(maxsize=256)
def _city_by_name(name: str) -> dict[str, Any] | None:
    r = row(
        "SELECT city_id, name AS city_name, state, country_code, timezone "
        "FROM cities WHERE lower(name) = lower(?) LIMIT 1",
        (name,),
    )
    return r or row(
        "SELECT city_id, name AS city_name, state, country_code, timezone "
        "FROM cities WHERE lower(name) LIKE lower(?) LIMIT 1",
        (f"%{name}%",),
    )


def resolve_city(text: str) -> dict[str, Any] | None:
    """IATA code, common name, or exact dataset name -> city row (fresh copy)."""
    if not text:
        return None
    key = text.strip().upper()
    for candidate in (IATA_TO_CITY.get(key), CITY_ALIASES.get(key), text.strip()):
        if not candidate:
            continue
        found = _city_by_name(candidate)
        if found:
            return dict(found)
    return None


def list_cities(country_code: str = "IN") -> list[dict[str, Any]]:
    return rows(
        "SELECT city_id, name AS city_name, state, country_code FROM cities "
        "WHERE country_code = ? ORDER BY name",
        (country_code,),
    )


# ---------------------------------------------------------------------------
# Packages & components
# ---------------------------------------------------------------------------

def packages_for_city(city_id: str, min_days: int | None = None, max_days: int | None = None,
                       limit: int = 20) -> list[dict[str, Any]]:
    sql = ("SELECT package_id, city_id, name, description, duration_days, base_price, "
           "currency, theme FROM tour_packages WHERE status='active' AND city_id=?")
    params: list[Any] = [city_id]
    if min_days:
        sql += " AND duration_days >= ?"; params.append(min_days)
    if max_days:
        sql += " AND duration_days <= ?"; params.append(max_days)
    sql += " ORDER BY base_price LIMIT ?"; params.append(limit)
    return rows(sql, tuple(params))


def package_components(package_id: str) -> list[dict[str, Any]]:
    return rows(
        "SELECT component_id, package_id, component_type, title, day_index, slot, "
        "quantity, price_delta, currency, is_optional, is_swappable, swap_group "
        "FROM package_components WHERE package_id=? ORDER BY day_index, component_type",
        (package_id,),
    )


def component_alternatives(package_id: str, component_id: str) -> list[dict[str, Any]]:
    target = row(
        "SELECT swap_group, component_type FROM package_components "
        "WHERE package_id=? AND component_id=?",
        (package_id, component_id),
    )
    if not target or not target.get("swap_group"):
        return []
    return rows(
        "SELECT component_id, title, price_delta, component_type FROM package_components "
        "WHERE package_id=? AND swap_group=? AND component_id != ? AND is_swappable=1",
        (package_id, target["swap_group"], component_id),
    )


# ---------------------------------------------------------------------------
# Guides
# ---------------------------------------------------------------------------

def match_guides(city_id: str, languages: list[str] | None, specialisation: str | None,
                  max_day_rate: Decimal | None, limit: int = 12) -> list[dict[str, Any]]:
    sql = ("SELECT g.guide_id, g.city_id, g.display_name, g.languages, g.specialisation, "
           "g.day_rate, g.half_day_rate, g.rating, g.review_count, g.years_experience, "
           "g.certified, g.bio, c.name AS city_name FROM tour_guides g "
           "LEFT JOIN cities c ON c.city_id = g.city_id WHERE g.city_id = ? AND g.status='active'")
    params: list[Any] = [city_id]
    if specialisation:
        sql += " AND g.specialisation = ?"; params.append(specialisation)
    sql += " ORDER BY g.rating DESC LIMIT ?"; params.append(limit)
    candidates = rows(sql, tuple(params))

    out = []
    for g in candidates:
        if max_day_rate is not None and d(g["day_rate"]) > max_day_rate:
            continue
        if languages:
            guide_langs = {lg.strip().lower() for lg in (g["languages"] or "").split(",")}
            wanted = {lg.strip().lower() for lg in languages}
            if not (guide_langs & wanted):
                continue
        out.append(g)
    return out


# ---------------------------------------------------------------------------
# Market benchmark — the dual-itinerary feature's data source
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1024)
def _benchmark_cached(city_id: str, duration_days: int) -> dict[str, Any] | None:
    city = row("SELECT city_id, name AS city_name, state, country_code FROM cities WHERE city_id=?",
               (city_id,))
    if not city:
        return None

    def per_day_stats(where: str, params: tuple) -> dict[str, Any] | None:
        pkgs = rows(
            f"SELECT base_price, duration_days FROM tour_packages "
            f"WHERE status='active' AND duration_days > 0 AND {where}", params,
        )
        if not pkgs:
            return None
        per_day = sorted(d(p["base_price"]) / p["duration_days"] for p in pkgs)
        n = len(per_day)
        avg = sum(per_day) / n
        return {"avg": avg, "min": per_day[0], "max": per_day[-1], "n": n}

    for level, where, params in (
        ("city", "city_id = ?", (city_id,)),
        ("state", "city_id IN (SELECT city_id FROM cities WHERE state = ?)", (city["state"],)),
        ("country", "city_id IN (SELECT city_id FROM cities WHERE country_code = ?)", (city["country_code"],)),
    ):
        stats = per_day_stats(where, params)
        if stats:
            return {
                "fallback_level": level,
                "city_name": city["city_name"],
                "sample_size": stats["n"],
                "price_per_day_avg": stats["avg"],
                "total_avg": stats["avg"] * duration_days,
                "total_min": stats["min"] * duration_days,
                "total_max": stats["max"] * duration_days,
            }
    return None


def market_benchmark(city_id: str, duration_days: int) -> dict[str, Any] | None:
    cached = _benchmark_cached(city_id, duration_days)
    return dict(cached) if cached else None
