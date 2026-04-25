"""
Market condition alert triggers.

Each function compares a current MarketSnapshot against a prior snapshot
(or against static absolute thresholds when no prior is available) and
returns an Alert if a threshold is crossed, else None.

Thresholds are calibrated to the owner's risk priority order:
  high vacancy > regulatory > cap expenses > market softening
"""

from __future__ import annotations

from .models import Alert, AlertType, AlertSeverity
from real_estate_agent.scoring.models import MarketSnapshot

# ── Thresholds ────────────────────────────────────────────────────────────────
OCC_DROP_CRITICAL_PP   = 0.15   # 15+ percentage-point drop → CRITICAL
OCC_DROP_HIGH_PP       = 0.08   # 8–15 pp drop → HIGH
OCC_ABSOLUTE_LOW       = 0.50   # below 50% annual occ → flag regardless

ADR_DROP_HIGH_PCT      = 0.10   # 10%+ MoM drop → HIGH
ADR_DROP_MEDIUM_PCT    = 0.06   # 6–10% drop → MEDIUM
ADR_SURGE_PCT          = 0.10   # 10%+ surge → positive alert (raise prices)

SUPPLY_SURGE_HIGH      = 0.20   # 20%+ new listings YoY → HIGH
SUPPLY_SURGE_MEDIUM    = 0.15   # 15–20% → MEDIUM

PRICE_DROP_HIGH_PCT    = 0.05   # 5%+ QoQ appreciation going negative → HIGH
PRICE_SURGE_PCT        = 0.08   # 8%+ appreciation → sell-side alert (positive)


def _alert_id(market_id: str, alert_type: AlertType, date: str) -> str:
    return f"{market_id}__{alert_type.value}__{date}"


def check_occupancy(
    current: MarketSnapshot,
    prior: MarketSnapshot | None,
    date: str = "2025-04-25",
) -> Alert | None:
    occ_c = current.annual_occupancy_rate
    occ_p = prior.annual_occupancy_rate if prior else None

    # Delta-based trigger
    if occ_p is not None:
        delta = occ_c - occ_p
        if delta <= -OCC_DROP_CRITICAL_PP:
            sev = AlertSeverity.CRITICAL
            drop_desc = f"{abs(delta)*100:.1f} percentage-point collapse"
        elif delta <= -OCC_DROP_HIGH_PP:
            sev = AlertSeverity.HIGH
            drop_desc = f"{abs(delta)*100:.1f} percentage-point decline"
        else:
            return None

        return Alert(
            alert_id=_alert_id(current.market_id, AlertType.MKT_OCCUPANCY_DROP, date),
            alert_type=AlertType.MKT_OCCUPANCY_DROP,
            severity=sev,
            market_id=current.market_id,
            market_name=current.name,
            title=f"Occupancy drop in {current.name}: {occ_p*100:.1f}% → {occ_c*100:.1f}%",
            body=(
                f"{current.name} annual occupancy fell {drop_desc} week-over-week, "
                f"from {occ_p*100:.1f}% to {occ_c*100:.1f}%. "
                f"Your #1 risk (high vacancy) is activating in this market. "
                f"Check whether a local event, new supply, or regulatory change is driving this."
            ),
            action_required=(
                "Review AirDNA market detail for this region. Compare competitor pricing. "
                "If you own in this market, consider a short-term pricing discount to maintain occupancy."
            ),
            triggered_at=date,
            source="market_trigger",
            metric_label="Annual occupancy",
            metric_before=occ_p,
            metric_after=occ_c,
        )

    # Absolute threshold (no prior available)
    if occ_c < OCC_ABSOLUTE_LOW:
        return Alert(
            alert_id=_alert_id(current.market_id, AlertType.MKT_OCCUPANCY_DROP, date),
            alert_type=AlertType.MKT_OCCUPANCY_DROP,
            severity=AlertSeverity.MEDIUM,
            market_id=current.market_id,
            market_name=current.name,
            title=f"Low occupancy in {current.name}: {occ_c*100:.1f}%",
            body=f"Annual occupancy in {current.name} is {occ_c*100:.1f}%, below the 50% minimum threshold.",
            action_required="Verify data freshness. If accurate, deprioritize this market.",
            triggered_at=date,
            source="market_trigger",
            metric_label="Annual occupancy",
            metric_after=occ_c,
        )
    return None


def check_adr(
    current: MarketSnapshot,
    prior: MarketSnapshot | None,
    date: str = "2025-04-25",
) -> list[Alert]:
    if prior is None:
        return []

    adr_c = current.median_adr_3bd
    adr_p = prior.median_adr_3bd
    pct_change = (adr_c - adr_p) / adr_p

    alerts = []

    if pct_change <= -ADR_DROP_HIGH_PCT:
        alerts.append(Alert(
            alert_id=_alert_id(current.market_id, AlertType.MKT_ADR_DROP, date),
            alert_type=AlertType.MKT_ADR_DROP,
            severity=AlertSeverity.HIGH,
            market_id=current.market_id,
            market_name=current.name,
            title=f"ADR falling in {current.name}: ${adr_p:.0f} → ${adr_c:.0f} ({pct_change*100:+.1f}%)",
            body=(
                f"Average daily rates in {current.name} dropped {abs(pct_change)*100:.1f}% "
                f"from ${adr_p:.0f} to ${adr_c:.0f}. This could indicate oversupply, "
                f"softening demand, or seasonal pricing pressure beyond normal patterns."
            ),
            action_required=(
                "Compare your property's nightly rate against top 10 competitors. "
                "Check if supply (active listings) increased concurrently. "
                "If demand-driven, consider dynamic pricing adjustments."
            ),
            triggered_at=date,
            source="market_trigger",
            metric_label="Median ADR (3bd)",
            metric_before=adr_p,
            metric_after=adr_c,
        ))
    elif pct_change <= -ADR_DROP_MEDIUM_PCT:
        alerts.append(Alert(
            alert_id=_alert_id(current.market_id, AlertType.MKT_ADR_DROP, date),
            alert_type=AlertType.MKT_ADR_DROP,
            severity=AlertSeverity.MEDIUM,
            market_id=current.market_id,
            market_name=current.name,
            title=f"ADR moderately lower in {current.name}: {pct_change*100:+.1f}%",
            body=f"ADR slipped {abs(pct_change)*100:.1f}% from ${adr_p:.0f} to ${adr_c:.0f}. Monitor next 2 weeks.",
            action_required="Watch for continued decline before adjusting strategy.",
            triggered_at=date,
            source="market_trigger",
            metric_label="Median ADR (3bd)",
            metric_before=adr_p,
            metric_after=adr_c,
        ))

    if pct_change >= ADR_SURGE_PCT:
        alerts.append(Alert(
            alert_id=_alert_id(current.market_id, AlertType.MKT_ADR_SURGE, date),
            alert_type=AlertType.MKT_ADR_SURGE,
            severity=AlertSeverity.MEDIUM,
            market_id=current.market_id,
            market_name=current.name,
            title=f"ADR surging in {current.name}: {pct_change*100:+.1f}% — raise prices or sell signal",
            body=(
                f"ADR in {current.name} jumped {pct_change*100:.1f}% to ${adr_c:.0f}. "
                f"If you own here: raise nightly rates immediately. "
                f"If prospective buyer: market strengthening, but competition for inventory will increase."
            ),
            action_required="If owner: update nightly rates now. If prospective: accelerate property search.",
            triggered_at=date,
            source="market_trigger",
            positive=True,
            metric_label="Median ADR (3bd)",
            metric_before=adr_p,
            metric_after=adr_c,
        ))

    return alerts


def check_supply(
    current: MarketSnapshot,
    prior: MarketSnapshot | None,
    date: str = "2025-04-25",
) -> Alert | None:
    growth = current.listings_yoy_growth

    if growth >= SUPPLY_SURGE_HIGH:
        sev = AlertSeverity.HIGH
    elif growth >= SUPPLY_SURGE_MEDIUM:
        sev = AlertSeverity.MEDIUM
    else:
        return None

    # Only fire if this is worse than prior (avoid re-alerting same condition)
    if prior and prior.listings_yoy_growth >= growth:
        return None

    return Alert(
        alert_id=_alert_id(current.market_id, AlertType.MKT_SUPPLY_SURGE, date),
        alert_type=AlertType.MKT_SUPPLY_SURGE,
        severity=sev,
        market_id=current.market_id,
        market_name=current.name,
        title=f"Supply surge in {current.name}: +{growth*100:.0f}% new listings YoY",
        body=(
            f"Active STR listings in {current.name} grew {growth*100:.0f}% year-over-year "
            f"to {current.active_listings:,} units. "
            f"Increased competition will put downward pressure on occupancy and ADR "
            f"unless demand grows proportionally."
        ),
        action_required=(
            "Review competitor pricing strategy. Ensure your property's amenities, "
            "photography, and review score differentiate it from new supply."
        ),
        triggered_at=date,
        source="market_trigger",
        metric_label="Listings YoY growth",
        metric_after=growth,
    )


def check_home_price(
    current: MarketSnapshot,
    prior: MarketSnapshot | None,
    date: str = "2025-04-25",
) -> Alert | None:
    appr = current.home_price_yoy_appreciation

    if appr >= PRICE_SURGE_PCT:
        return Alert(
            alert_id=_alert_id(current.market_id, AlertType.MKT_PRICE_SURGE, date),
            alert_type=AlertType.MKT_PRICE_SURGE,
            severity=AlertSeverity.LOW,
            market_id=current.market_id,
            market_name=current.name,
            title=f"Strong appreciation in {current.name}: +{appr*100:.1f}% YoY",
            body=(
                f"Home values in {current.name} are appreciating at {appr*100:.1f}% YoY. "
                f"If you own here, your equity is growing faster than baseline. "
                f"Consider whether this is the right time to lock in gains via a sale or 1031 exchange."
            ),
            action_required="Review portfolio. If holding, no action needed. If sell criteria met, engage agent.",
            triggered_at=date,
            source="market_trigger",
            positive=True,
            metric_label="Home price YoY appreciation",
            metric_after=appr,
        )

    if appr < PRICE_DROP_HIGH_PCT * -1:
        return Alert(
            alert_id=_alert_id(current.market_id, AlertType.MKT_PRICE_DROP, date),
            alert_type=AlertType.MKT_PRICE_DROP,
            severity=AlertSeverity.HIGH,
            market_id=current.market_id,
            market_name=current.name,
            title=f"Home values declining in {current.name}: {appr*100:+.1f}% YoY",
            body=(
                f"Median home prices in {current.name} are declining at {appr*100:.1f}% YoY. "
                f"This directly impacts your equity position and exit proceeds. "
                f"Monitor for a second consecutive quarter of decline — that crosses the 18-month exit evaluation trigger."
            ),
            action_required="Run updated pro forma with current values. If 18-month trajectory shows >-$18k cumulative, activate exit evaluation.",
            triggered_at=date,
            source="market_trigger",
            metric_label="Home price YoY appreciation",
            metric_after=appr,
        )

    return None


def run_all_market_triggers(
    current: MarketSnapshot,
    prior: MarketSnapshot | None,
    date: str = "2025-04-25",
) -> list[Alert]:
    alerts: list[Alert] = []

    a = check_occupancy(current, prior, date)
    if a:
        alerts.append(a)

    alerts.extend(check_adr(current, prior, date))

    a = check_supply(current, prior, date)
    if a:
        alerts.append(a)

    a = check_home_price(current, prior, date)
    if a:
        alerts.append(a)

    return alerts
