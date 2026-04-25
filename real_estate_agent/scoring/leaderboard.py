from __future__ import annotations

from .models import MarketScore, MarketCategory, RegulatoryStatus
from .factors import WEIGHTS


_CATEGORY_LABEL = {
    MarketCategory.COASTAL_NC: "Coastal NC",
    MarketCategory.COASTAL_SC: "Coastal SC",
    MarketCategory.LAKE_NC: "Lake NC",
    MarketCategory.MOUNTAIN_NC: "Mountain NC",
}

_REG_LABEL = {
    RegulatoryStatus.STABLE: "Stable",
    RegulatoryStatus.EVOLVING_BENIGN: "Evolving (benign)",
    RegulatoryStatus.EVOLVING_RISKY: "Evolving (RISKY)",
    RegulatoryStatus.RESTRICTIVE: "RESTRICTIVE",
}

_REG_FLAG = {
    RegulatoryStatus.STABLE: " ",
    RegulatoryStatus.EVOLVING_BENIGN: "~",
    RegulatoryStatus.EVOLVING_RISKY: "!",
    RegulatoryStatus.RESTRICTIVE: "X",
}


def _delta_str(delta: float | None) -> str:
    if delta is None:
        return "  new "
    if delta > 0:
        return f" +{delta:.1f}"
    if delta < 0:
        return f"  {delta:.1f}"
    return "   0.0"


def print_leaderboard(scores: list[MarketScore], title: str = "MARKET LEADERBOARD") -> None:
    W = 110
    print(f"\n{'═' * W}")
    print(f"  {title}")
    print(f"  Weights: " + "  |  ".join(f"{k} {v*100:.0f}%" for k, v in WEIGHTS.items()))
    print(f"{'═' * W}")

    header = (
        f"  {'Rk':<3}  {'Market':<36}  {'Cat':<12}  {'Score':>5}  {'Δ':>6}  "
        f"{'Occ%':>5}  {'ADR':>5}  {'RevPAN':>7}  {'Reg':>18}  {'Viable':<14}"
    )
    print(header)
    print(f"  {'─' * (W - 2)}")

    for ms in scores:
        m = ms.market
        reg_label = _REG_LABEL[m.regulatory_status]
        reg_flag = _REG_FLAG[m.regulatory_status]
        viable = []
        if ms.viable_for_cash_purchase:
            viable.append("Cash")
        if ms.viable_for_financed_purchase:
            viable.append("Financed")
        viable_str = "+".join(viable) if viable else "—"

        hoa_warn = " [HOA!]" if m.hoa_str_risk else ""
        delta_s = _delta_str(ms.delta)

        print(
            f"  {ms.rank:<3}  {(m.name + hoa_warn):<36}  {_CATEGORY_LABEL[m.category]:<12}  "
            f"{ms.composite_score:>5.1f}  {delta_s:>6}  "
            f"{m.annual_occupancy_rate*100:>4.0f}%  "
            f"${m.median_adr_3bd:>4.0f}  "
            f"${m.annual_revpan:>5.0f}/n  "
            f"{reg_flag} {reg_label:<16}  "
            f"{viable_str}"
        )

    print(f"\n  Legend: Δ = score change vs prior week  |  [HOA!] = HOA STR ban risk")
    print(f"          Reg flags: ' '=Stable  '~'=Evolving(benign)  '!'=Evolving(RISKY)  'X'=RESTRICTIVE")
    print(f"          Viable: Cash/Financed = meets minimum occupancy+RevPAN thresholds for that purchase type")
    print(f"{'═' * W}\n")


def print_market_detail(ms: MarketScore) -> None:
    m = ms.market
    W = 72
    print(f"\n{'═' * W}")
    print(f"  MARKET DETAIL  ·  #{ms.rank}  {m.name}")
    print(f"  {m.state}  |  {_CATEGORY_LABEL[m.category]}  |  Data: {m.data_date}  ({m.data_source})")
    print(f"{'═' * W}")

    print(f"\n  COMPOSITE SCORE:  {ms.composite_score:.1f} / 100", end="")
    if ms.delta is not None:
        arrow = "↑" if ms.delta > 0 else "↓" if ms.delta < 0 else "→"
        print(f"   {arrow} {ms.delta:+.1f} vs prior week", end="")
    print()

    if ms.regulatory_alert:
        print(f"\n  ⚠  REGULATORY ALERT: {m.regulatory_notes}")
    if m.hoa_str_risk:
        print(f"\n  ⚠  HOA RISK: Many properties in this market have HOA/POA rules restricting STR.")

    print(f"\n  {'Factor':<18}  {'Raw Value':<22}  {'Score':>6}  {'Weight':>7}  {'Wtd':>6}  Note")
    print(f"  {'─' * 68}")
    for f in sorted(ms.factors, key=lambda x: x.weighted, reverse=True):
        print(f"  {f.name:<18}  {str(f.raw_value):<22}  {f.score:>6.1f}  {f.weight*100:>6.0f}%  {f.weighted:>6.1f}  {f.note}")

    print(f"\n  MARKET SNAPSHOT")
    print(f"  {'─' * 50}")
    print(f"  Annual occupancy:     {m.annual_occupancy_rate*100:.1f}%")
    print(f"  Peak occupancy:       {m.peak_occupancy_rate*100:.1f}%  (Jun–Aug)")
    print(f"  Median ADR (3bd):     ${m.median_adr_3bd:,.0f}/night")
    print(f"  ADR YoY growth:       {m.adr_yoy_growth*100:+.1f}%")
    print(f"  Annual RevPAN:        ${m.annual_revpan:,.0f}/available night")
    print(f"  Active listings:      {m.active_listings:,}")
    print(f"  Listings YoY growth:  {m.listings_yoy_growth*100:+.1f}%")
    print(f"  Median home price:    ${m.median_home_price:,.0f}")
    print(f"  Home price YoY:       {m.home_price_yoy_appreciation*100:+.1f}%")
    print(f"  Airport:              {m.nearest_airport_code}  ({m.nearest_airport_drive_min} min drive)")
    print(f"  Golf courses (30mi):  {m.golf_courses_30mi}")
    print(f"  Regulatory status:    {_REG_LABEL[m.regulatory_status]}")
    print(f"  Reg notes:            {m.regulatory_notes}")

    print(f"\n  VIABILITY")
    print(f"  Cash purchase:        {'✓  Meets minimum thresholds' if ms.viable_for_cash_purchase else '✗  Below minimum RevPAN or occupancy'}")
    print(f"  Financed purchase:    {'✓  Meets minimum thresholds' if ms.viable_for_financed_purchase else '✗  Below RevPAN or price threshold for financed deal'}")
    print(f"{'═' * W}\n")


def print_alerts(scores: list[MarketScore]) -> None:
    alerts = [ms for ms in scores if ms.regulatory_alert]
    if not alerts:
        print("\n  No regulatory alerts this week.\n")
        return
    print(f"\n{'!' * 60}")
    print(f"  REGULATORY ALERTS  ({len(alerts)} market(s))")
    print(f"{'!' * 60}")
    for ms in alerts:
        print(f"\n  [{ms.rank}] {ms.market.name}")
        print(f"      Status: {_REG_LABEL[ms.market.regulatory_status]}")
        print(f"      {ms.market.regulatory_notes}")
    print()
