"""
5-factor property scoring. Each factor returns a FactorScore (0–100).
Composite = weighted sum. Weights reflect owner's stated priorities.
"""

from __future__ import annotations

from .models import PropertyListing, FactorScore
from real_estate_agent.scoring.models import MarketScore, RegulatoryStatus
from real_estate_agent.scoring.normalizer import normalize, airport_score as _airport_score

WEIGHTS = {
    "financial":  0.25,   # monthly CF vs -$1k floor (primary filter outcome)
    "market":     0.20,   # region composite score overlay
    "location":   0.20,   # beach proximity + airport
    "value":      0.20,   # price vs market median, DOM, price reductions
    "risk":       0.15,   # HOA, age, flood zone, regulatory
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def _financial_score(listing: PropertyListing) -> FactorScore:
    """
    Score based on estimated cash monthly CF (cash purchase scenario).
    Anchored at -$1,000/mo floor (owner's stated tolerance).
    """
    cf = listing.estimated_monthly_cf_cash
    if cf is None:
        score, note = 50.0, "Not yet enriched"
    elif cf >= 500:
        score = 100.0
        note = f"Cash CF: +${cf:,.0f}/mo  (strongly positive)"
    elif cf >= 0:
        score = 80.0 + (cf / 500.0) * 20.0
        note = f"Cash CF: +${cf:,.0f}/mo  (positive)"
    elif cf >= -500:
        score = 60.0 + ((cf + 500) / 500.0) * 20.0
        note = f"Cash CF: ${cf:,.0f}/mo  (within floor)"
    elif cf >= -1_000:
        score = 40.0 + ((cf + 1_000) / 500.0) * 20.0
        note = f"Cash CF: ${cf:,.0f}/mo  (at floor)"
    elif cf >= -2_000:
        score = 20.0 + ((cf + 2_000) / 1_000.0) * 20.0
        note = f"Cash CF: ${cf:,.0f}/mo  (BELOW floor)"
    else:
        score = max(0.0, 20.0 + (cf + 2_000) / 1_000.0 * 20.0)
        note = f"Cash CF: ${cf:,.0f}/mo  (well below floor)"

    dscr_note = ""
    if listing.estimated_monthly_cf_dscr is not None:
        dscr_note = f"  |  DSCR CF: ${listing.estimated_monthly_cf_dscr:,.0f}/mo"

    w = WEIGHTS["financial"]
    return FactorScore("financial", score, w, score * w, note + dscr_note)


def _market_score(market_composite: float) -> FactorScore:
    """Direct overlay of the region's composite score."""
    score = market_composite  # already 0–100
    w = WEIGHTS["market"]
    return FactorScore("market", score, w, score * w, f"Region score: {market_composite:.1f}/100")


def _location_score(listing: PropertyListing) -> FactorScore:
    # Beach proximity
    if listing.beach_distance_miles is not None and listing.beach_distance_miles <= 10:
        d = listing.beach_distance_miles
        if d <= 0.25:
            beach = 100.0
        elif d <= 1.0:
            beach = 90.0
        elif d <= 3.0:
            beach = 78.0
        elif d <= 5.0:
            beach = 64.0
        else:
            beach = 50.0
    elif listing.has_pool:
        beach = 48.0   # pool is alternative; lower than actual beach proximity
    else:
        beach = 15.0   # fails hard filter but score it anyway for transparency

    airport = _airport_score(listing.airport_drive_min)

    # Flood zone bonus/penalty applied to location
    flood_adj = 0.0
    if listing.flood_zone == "VE":
        flood_adj = -18.0
    elif listing.flood_zone in ("AE", "A"):
        flood_adj = -8.0
    elif listing.flood_zone == "X":
        flood_adj = 5.0

    score = max(0.0, min(100.0, beach * 0.60 + airport * 0.40 + flood_adj))

    beach_desc = f"{listing.beach_distance_miles:.1f}mi to beach" if listing.beach_distance_miles else "pool (beach N/A)"
    note = f"{beach_desc}  |  {listing.airport_code} {listing.airport_drive_min}min  |  flood zone {listing.flood_zone}"
    w = WEIGHTS["location"]
    return FactorScore("location", score, w, score * w, note)


def _value_score(listing: PropertyListing, market_snapshot) -> FactorScore:
    median = market_snapshot.median_home_price if market_snapshot else listing.price

    # Price vs market median (cheaper relative = better deal signal)
    price_ratio = listing.price / median if median > 0 else 1.0
    price_sub = normalize(price_ratio, 0.60, 1.40, invert=True)

    # DOM: longer DOM suggests negotiation leverage (up to 180 days)
    dom_sub = normalize(float(listing.days_on_market), 0.0, 180.0)

    # Price reduction from original list
    reduction_sub = normalize(listing.price_reduction_pct, 0.0, 0.12)

    score = price_sub * 0.50 + dom_sub * 0.30 + reduction_sub * 0.20

    note = (
        f"${listing.price:,.0f} vs ${median:,.0f} median ({price_ratio*100:.0f}%)  |  "
        f"DOM {listing.days_on_market}  |  "
        f"reduced {listing.price_reduction_pct*100:.1f}% (${listing.price_reduction:,.0f})"
    )
    w = WEIGHTS["value"]
    return FactorScore("value", score, w, score * w, note)


def _risk_score(listing: PropertyListing, market_snapshot) -> FactorScore:
    score = 100.0
    notes = []

    # HOA
    if listing.has_hoa:
        if listing.hoa_str_permitted is False:
            score -= 60.0
            notes.append("HOA bans STR")
        elif listing.hoa_str_permitted is None:
            score -= 20.0
            notes.append("HOA — STR permission unknown")
        else:
            if listing.hoa_monthly > 200:
                score -= 10.0
                notes.append(f"HOA ${listing.hoa_monthly:.0f}/mo")

    # Age penalty (closer to 20yr max = higher penalty)
    age = listing.age
    if age > 18:
        score -= 14.0
        notes.append(f"Age {age}yr — near max")
    elif age > 15:
        score -= 7.0
        notes.append(f"Age {age}yr")

    # Flood zone
    if listing.flood_zone == "VE":
        score -= 20.0
        notes.append("Flood zone VE (high risk)")
    elif listing.flood_zone in ("AE", "A"):
        score -= 10.0
        notes.append("Flood zone AE/A (moderate)")

    # Regulatory market risk
    if market_snapshot:
        if market_snapshot.regulatory_status == RegulatoryStatus.EVOLVING_RISKY:
            score -= 18.0
            notes.append("Market reg: EVOLVING RISKY")
        elif market_snapshot.regulatory_status == RegulatoryStatus.EVOLVING_BENIGN:
            score -= 5.0
            notes.append("Market reg: evolving (benign)")

    score = max(0.0, score)
    note = "  |  ".join(notes) if notes else "No major risk flags"
    w = WEIGHTS["risk"]
    return FactorScore("risk", score, w, score * w, note)


def score_property(listing: PropertyListing, market_score: MarketScore) -> list[FactorScore]:
    return [
        _financial_score(listing),
        _market_score(market_score.composite_score),
        _location_score(listing),
        _value_score(listing, listing.market_snapshot),
        _risk_score(listing, listing.market_snapshot),
    ]


_RECOMMENDATION = [
    (78, "Strong Buy Candidate"),
    (68, "Monitor Closely"),
    (58, "Investigate Further"),
    (0,  "Pass"),
]


def recommendation(composite: float) -> str:
    for threshold, label in _RECOMMENDATION:
        if composite >= threshold:
            return label
    return "Pass"
