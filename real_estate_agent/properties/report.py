from __future__ import annotations

from .models import PropertyScore, PropertyListing, FilterResult
from .scorer import WEIGHTS


def _c(v: float, sign: bool = False) -> str:
    prefix = "+" if sign and v >= 0 else ""
    return f"-${abs(v):,.0f}" if v < 0 else f"{prefix}${v:,.0f}"


def _pct(v: float | None) -> str:
    return "N/A" if v is None else f"{v*100:.1f}%"


_ACTION_COLOR = {
    "Strong Buy Candidate": "★★★",
    "Monitor Closely":      "★★ ",
    "Investigate Further":  "★  ",
    "Pass":                 "   ",
}


def print_property_table(scores: list[PropertyScore], title: str = "WEEKLY PROPERTY PICKS") -> None:
    W = 118
    print(f"\n{'═' * W}")
    print(f"  {title}")
    print(f"  Factor weights: " + "  |  ".join(f"{k} {v*100:.0f}%" for k, v in WEIGHTS.items()))
    print(f"{'═' * W}")

    hdr = (
        f"  {'Rk':<3}  {'Address':<36}  {'Mkt':>3}  {'Price':>10}  "
        f"{'Bd/Ba':>5}  {'Yr':>4}  {'Score':>5}  {'Action':<22}  "
        f"{'Cash CF':>9}  {'DSCR CF':>9}  {'IRR':>5}"
    )
    print(hdr)
    print(f"  {'─' * (W - 2)}")

    for ps in scores:
        l = ps.listing
        addr = f"{l.address}, {l.city}"[:35]
        mkt = l.market_id.split("_")[1].upper()[:3]
        bdba = f"{l.bedrooms}/{l.bathrooms:.0f}"
        cash_cf = f"${l.estimated_monthly_cf_cash:,.0f}/mo" if l.estimated_monthly_cf_cash is not None else "  N/A"
        dscr_cf = f"${l.estimated_monthly_cf_dscr:,.0f}/mo" if l.estimated_monthly_cf_dscr is not None else "  N/A"
        irr = _pct(l.estimated_irr_cash_5yr)
        action = _ACTION_COLOR.get(ps.recommendation, "   ") + " " + ps.recommendation

        print(
            f"  {ps.rank:<3}  {addr:<36}  {mkt:>3}  ${l.price:>9,.0f}  "
            f"{bdba:>5}  {l.year_built:>4}  {ps.composite_score:>5.1f}  {action:<22}  "
            f"{cash_cf:>9}  {dscr_cf:>9}  {irr:>5}"
        )

    print(f"\n  Cash CF and DSCR CF = estimated monthly cash flow (cash purchase vs 30% down DSCR @ 7.75%)")
    print(f"  IRR = 5-year IRR including appreciation and sale proceeds (cash purchase scenario)")
    print(f"{'═' * W}\n")


def print_property_detail(ps: PropertyScore) -> None:
    l = ps.listing
    W = 74
    print(f"\n{'═' * W}")
    print(f"  #{ps.rank}  {l.address}, {l.city}, {l.state} {l.zip_code}")
    print(f"  {ps.recommendation}  ·  Score {ps.composite_score:.1f}/100")
    print(f"  {l.url}")
    print(f"{'═' * W}")

    print(f"\n  Price:              ${l.price:,.0f}  ({l.bedrooms}bd/{l.bathrooms:.0f}ba  {l.sqft:,} sqft)")
    print(f"  Year built:         {l.year_built}  ({l.age} years old)")
    print(f"  Price/sqft:         ${l.price_per_sqft:,.0f}")
    print(f"  DOM:                {l.days_on_market} days  |  Original: ${l.original_list_price:,.0f}  |  Reduced: ${l.price_reduction:,.0f} ({l.price_reduction_pct*100:.1f}%)")
    print(f"  HOA:                {'None' if not l.has_hoa else f'${l.hoa_monthly:.0f}/mo — STR permitted: {l.hoa_str_permitted}'}")
    print(f"  Pool:               {'Yes' if l.has_pool else 'No'}")
    print(f"  Beach:              {f'{l.beach_distance_miles:.1f} mi' if l.beach_distance_miles else 'N/A'}")
    print(f"  Airport:            {l.airport_code}  ({l.airport_drive_min} min)")
    print(f"  Flood zone:         {l.flood_zone}")

    if l.market_snapshot:
        m = l.market_snapshot
        print(f"\n  MARKET:  {m.name}  |  Annual occ {m.annual_occupancy_rate*100:.0f}%  |  ADR ${m.median_adr_3bd:.0f}  |  RevPAN ${m.annual_revpan:.0f}")

    print(f"\n  FINANCIAL ESTIMATES (market avg occupancy / ADR)")
    print(f"  EGI (annual):         ${l.estimated_egi_annual:,.0f}" if l.estimated_egi_annual else "  EGI: N/A")
    if l.estimated_monthly_cf_cash is not None:
        cf_flag = "  ✓ within -$1k/mo floor" if l.estimated_monthly_cf_cash >= -1000 else "  ✗ BELOW -$1k/mo floor"
        print(f"  Cash CF (monthly):    ${l.estimated_monthly_cf_cash:,.0f}/mo{cf_flag}")
    if l.estimated_monthly_cf_dscr is not None:
        print(f"  DSCR CF (monthly):    ${l.estimated_monthly_cf_dscr:,.0f}/mo  (30% down @ 7.75%)")
    if l.estimated_irr_cash_5yr is not None:
        print(f"  5-yr IRR (cash):      {l.estimated_irr_cash_5yr*100:.1f}%")

    print(f"\n  SCORING BREAKDOWN")
    print(f"  {'Factor':<14}  {'Score':>6}  {'Weight':>7}  {'Wtd':>6}  Note")
    print(f"  {'─' * 68}")
    for f in sorted(ps.factors, key=lambda x: x.weighted, reverse=True):
        print(f"  {f.name:<14}  {f.score:>6.1f}  {f.weight*100:>6.0f}%  {f.weighted:>6.1f}  {f.note}")
    print(f"  {'─' * 68}")
    print(f"  {'COMPOSITE':<14}  {ps.composite_score:>6.1f}")
    print(f"{'═' * W}\n")


def print_rejected(rejected: list[tuple[PropertyListing, FilterResult]]) -> None:
    print(f"\n{'─' * 74}")
    print(f"  FILTERED OUT  ({len(rejected)} properties failed hard filters)")
    print(f"{'─' * 74}")
    for l, fr in rejected:
        print(f"  ✗  {l.address}, {l.city}  (${l.price:,.0f})")
        for reason in fr.failed_reasons:
            print(f"       → {reason}")
    print()
