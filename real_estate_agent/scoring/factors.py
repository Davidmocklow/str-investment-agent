"""
One function per scoring factor, each returning a FactorScore.

Weights reflect owner priorities:
  - Appreciate + personal use primary objective
  - Vacancy risk is #1 fear, then regulatory, then cap-ex, then softening
  - High seasonal demand preferred
  - Airport proximity hard preference (<60 min)
  - Golf is a plus
  - Priority: coastal > lake > mountain
"""

from .models import MarketSnapshot, FactorScore, RegulatoryStatus
from .normalizer import normalize, airport_score, beach_access_score, REGULATORY_SCORES

# ── Weights (must sum to 1.0) ─────────────────────────────────────────────────
WEIGHTS = {
    "regulatory":     0.18,   # #2 fear; highest single weight — a ban destroys the investment
    "occupancy":      0.15,   # #1 fear is vacancy; blended annual rate
    "adr_trend":      0.12,   # rising ADR = stronger market = raise prices or sell
    "appreciation":   0.12,   # primary objective is appreciation
    "revpan":         0.10,   # combined efficiency metric
    "seasonality":    0.08,   # prefers high seasonal peak (maximize summer revenue)
    "supply_growth":  0.08,   # more competition dilutes occupancy
    "airport":        0.07,   # guest convenience; hard preference <60 min
    "beach":          0.05,   # coastal > lake > mountain
    "golf":           0.05,   # nice-to-have
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


def score_regulatory(m: MarketSnapshot) -> FactorScore:
    raw = m.regulatory_status.value
    base = REGULATORY_SCORES.get(raw, 50.0)
    # Additional penalty if many HOAs ban STR in the market
    score = base - (12.0 if m.hoa_str_risk else 0.0)
    score = max(0.0, score)
    note = m.regulatory_notes[:80]
    w = WEIGHTS["regulatory"]
    return FactorScore("regulatory", raw, score, w, score * w, note)


def score_occupancy(m: MarketSnapshot) -> FactorScore:
    # Blended annual; range calibrated to NC/SC market space (40% low, 80% high)
    score = normalize(m.annual_occupancy_rate, 0.40, 0.80)
    note = f"Annual {m.annual_occupancy_rate*100:.1f}%  |  Peak {m.peak_occupancy_rate*100:.1f}%"
    w = WEIGHTS["occupancy"]
    return FactorScore("occupancy", m.annual_occupancy_rate, score, w, score * w, note)


def score_adr_trend(m: MarketSnapshot) -> FactorScore:
    # YoY ADR growth; range -8% (crash) to +12% (hot)
    score = normalize(m.adr_yoy_growth, -0.08, 0.12)
    note = f"ADR YoY {m.adr_yoy_growth*100:+.1f}%  |  Current ${m.median_adr_3bd:,.0f}/night"
    w = WEIGHTS["adr_trend"]
    return FactorScore("adr_trend", m.adr_yoy_growth, score, w, score * w, note)


def score_appreciation(m: MarketSnapshot) -> FactorScore:
    # Property value YoY; range 0% to 10%+
    score = normalize(m.home_price_yoy_appreciation, 0.0, 0.10)
    note = f"Home price YoY {m.home_price_yoy_appreciation*100:+.1f}%  |  Median ${m.median_home_price:,.0f}"
    w = WEIGHTS["appreciation"]
    return FactorScore("appreciation", m.home_price_yoy_appreciation, score, w, score * w, note)


def score_revpan(m: MarketSnapshot) -> FactorScore:
    # Revenue per available night (annualized); range $80 to $320
    score = normalize(m.annual_revpan, 80.0, 320.0)
    note = f"RevPAN ${m.annual_revpan:.0f}/night"
    w = WEIGHTS["revpan"]
    return FactorScore("revpan", m.annual_revpan, score, w, score * w, note)


def score_seasonality(m: MarketSnapshot) -> FactorScore:
    """
    Owner prefers high seasonal demand (peak summer concentration).
    Metric: how much peak occupancy exceeds annual average.
    Higher peak premium → higher score.
    Range: 5% premium (flat year-round) to 30% premium (strongly seasonal).
    """
    peak_premium = m.peak_occupancy_rate - m.annual_occupancy_rate
    score = normalize(peak_premium, 0.05, 0.30)
    note = f"Peak premium +{peak_premium*100:.1f}pp over annual avg"
    w = WEIGHTS["seasonality"]
    return FactorScore("seasonality", peak_premium, score, w, score * w, note)


def score_supply_growth(m: MarketSnapshot) -> FactorScore:
    # More new listings = more competition = worse; range 0% to 25% growth
    score = normalize(m.listings_yoy_growth, 0.0, 0.25, invert=True)
    direction = "supply contracting" if m.listings_yoy_growth < 0 else f"+{m.listings_yoy_growth*100:.1f}% new supply"
    note = f"{direction}  |  {m.active_listings:,} active listings"
    w = WEIGHTS["supply_growth"]
    return FactorScore("supply_growth", m.listings_yoy_growth, score, w, score * w, note)


def score_airport(m: MarketSnapshot) -> FactorScore:
    score = airport_score(m.nearest_airport_drive_min)
    label = "within preference" if m.nearest_airport_drive_min <= 60 else "EXCEEDS 60-min preference"
    note = f"{m.nearest_airport_code}  {m.nearest_airport_drive_min} min  ({label})"
    w = WEIGHTS["airport"]
    return FactorScore("airport", m.nearest_airport_drive_min, score, w, score * w, note)


def score_beach(m: MarketSnapshot) -> FactorScore:
    score = beach_access_score(m.beach_access_tier)
    tier_labels = {1: "Oceanfront", 2: "Coastal <5mi", 3: "Coastal 5-10mi", 4: "Lake/river", 5: "Mountain"}
    note = tier_labels.get(m.beach_access_tier, "Unknown")
    w = WEIGHTS["beach"]
    return FactorScore("beach", m.beach_access_tier, score, w, score * w, note)


def score_golf(m: MarketSnapshot) -> FactorScore:
    # Range: 0 courses (no golf) to 30+ (golf mecca like Myrtle Beach / Hilton Head)
    score = normalize(float(m.golf_courses_30mi), 0.0, 30.0)
    note = f"{m.golf_courses_30mi} courses within 30 mi"
    w = WEIGHTS["golf"]
    return FactorScore("golf", float(m.golf_courses_30mi), score, w, score * w, note)
