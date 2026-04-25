from .models import MarketSnapshot, MarketScore, RegulatoryStatus
from .factors import (
    score_regulatory, score_occupancy, score_adr_trend, score_appreciation,
    score_revpan, score_seasonality, score_supply_growth,
    score_airport, score_beach, score_golf,
)

# Thresholds for viability flags (aligned with financial model outputs)
CASH_VIABLE_MIN_OCCUPANCY = 0.55     # cash purchase needs reasonable annual occupancy
CASH_VIABLE_MIN_REVPAN = 120.0       # needs to generate enough revenue to cover ops
FINANCED_MIN_REVPAN = 200.0          # financed deals need stronger revenue to approach DSCR 1.1x
FINANCED_MAX_PRICE = 800_000         # above this, financed deals almost never pencil at current rates


def score_market(snapshot: MarketSnapshot) -> MarketScore:
    factors = [
        score_regulatory(snapshot),
        score_occupancy(snapshot),
        score_adr_trend(snapshot),
        score_appreciation(snapshot),
        score_revpan(snapshot),
        score_seasonality(snapshot),
        score_supply_growth(snapshot),
        score_airport(snapshot),
        score_beach(snapshot),
        score_golf(snapshot),
    ]

    composite = sum(f.weighted for f in factors)

    # Viability flags (informed by financial model learnings)
    viable_cash = (
        snapshot.annual_occupancy_rate >= CASH_VIABLE_MIN_OCCUPANCY
        and snapshot.annual_revpan >= CASH_VIABLE_MIN_REVPAN
        and snapshot.regulatory_status not in (RegulatoryStatus.RESTRICTIVE,)
    )
    viable_financed = (
        snapshot.annual_revpan >= FINANCED_MIN_REVPAN
        and snapshot.median_home_price <= FINANCED_MAX_PRICE
        and snapshot.regulatory_status not in (RegulatoryStatus.RESTRICTIVE, RegulatoryStatus.EVOLVING_RISKY)
    )

    reg_alert = snapshot.regulatory_status in (
        RegulatoryStatus.EVOLVING_RISKY, RegulatoryStatus.RESTRICTIVE
    )

    delta = None
    if snapshot.prior_composite_score is not None:
        delta = composite - snapshot.prior_composite_score

    return MarketScore(
        market=snapshot,
        factors=factors,
        composite_score=round(composite, 1),
        prior_composite=snapshot.prior_composite_score,
        delta=delta,
        regulatory_alert=reg_alert,
        viable_for_cash_purchase=viable_cash,
        viable_for_financed_purchase=viable_financed,
    )


def rank_markets(snapshots: list[MarketSnapshot]) -> list[MarketScore]:
    """Score and rank all markets. Returns sorted list (highest score first)."""
    scores = [score_market(s) for s in snapshots]
    scores.sort(key=lambda x: x.composite_score, reverse=True)
    for i, ms in enumerate(scores):
        ms.rank = i + 1
    return scores
