"""
NC/SC STR Investment Intelligence Dashboard.

Run:  streamlit run dashboard.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NC/SC STR Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_REPORT_PATH = Path(__file__).parent / "data" / "weekly_report.json"
_HISTORY_DIR = Path(__file__).parent / "data" / "scan_history"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .alert-critical { background: #2d1010; border-left: 4px solid #ff4b4b; padding: 1rem; border-radius: 4px; margin-bottom: 0.75rem; }
  .alert-high     { background: #2d1d10; border-left: 4px solid #ff9f36; padding: 1rem; border-radius: 4px; margin-bottom: 0.75rem; }
  .alert-medium   { background: #2d2a10; border-left: 4px solid #ffd236; padding: 1rem; border-radius: 4px; margin-bottom: 0.75rem; }
  .alert-low      { background: #102030; border-left: 4px solid #4b9eff; padding: 1rem; border-radius: 4px; margin-bottom: 0.75rem; }
  .metric-pos { color: #2ecc71; font-weight: bold; }
  .metric-neg { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_report(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def list_history() -> list[str]:
    if not _HISTORY_DIR.exists():
        return []
    return sorted(
        [p.stem for p in _HISTORY_DIR.glob("*.json")],
        reverse=True,
    )


if not _REPORT_PATH.exists():
    st.error("No scan data found. Run `python run_weekly_scan.py` to generate the first report.")
    st.code("python run_weekly_scan.py")
    st.stop()

report = load_report(str(_REPORT_PATH))
summary = report["summary"]
scan_date = report["scan_date"]
markets = report["markets"]
props_passed = report["properties"]["passed"]
props_rejected = report["properties"]["rejected"]
alerts_immediate = report["alerts"]["immediate"]
alerts_weekly = report["alerts"]["weekly"]


# ── Header ────────────────────────────────────────────────────────────────────
c_title, c_date = st.columns([3, 1])
with c_title:
    st.title("🏠 NC/SC STR Investment Intelligence")
with c_date:
    history = list_history()
    if len(history) > 1:
        selected = st.selectbox("Scan date", history, index=0, label_visibility="collapsed")
        if selected != scan_date:
            report = load_report(str(_HISTORY_DIR / f"{selected}.json"))
            summary = report["summary"]
            scan_date = report["scan_date"]
            markets = report["markets"]
            props_passed = report["properties"]["passed"]
            props_rejected = report["properties"]["rejected"]
            alerts_immediate = report["alerts"]["immediate"]
            alerts_weekly = report["alerts"]["weekly"]
    else:
        st.caption(f"Scan: **{scan_date}**")

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Properties Passed", summary["properties_passed"],
          f"{summary['properties_rejected']} filtered out")

imm = summary["alerts_immediate"]
new = summary["alerts_new"]
k2.metric("New Alerts", new, f"{imm} immediate" if imm else "none immediate",
          delta_color="inverse" if imm else "off")

if props_passed:
    top = props_passed[0]
    k3.metric("Top Score", f"{top['composite_score']:.0f}/100", top["city"])
    cf = top.get("estimated_monthly_cf_cash") or 0
    k4.metric("Top Cash CF", f"${cf:+,.0f}/mo", top["recommendation"].replace("★", "").strip())
    irr = top.get("estimated_irr_cash_5yr")
    k5.metric("Top IRR (cash)", f"{irr*100:.1f}%" if irr else "—", "5-yr vs 8% hurdle")

st.divider()


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_alerts, tab_props, tab_markets, tab_analyze = st.tabs([
    f"🚨 Alerts ({summary['alerts_new']} new)",
    f"🏆 Properties ({summary['properties_passed']} passed)",
    f"📊 Markets ({summary['markets_scored']} scored)",
    "🔍 Analyze a Property",
])


# ══════════════════════════════════════════════════════════════════════════════
# ALERTS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_alerts:

    _SEV_CLASS = {
        "critical": "alert-critical",
        "high": "alert-high",
        "medium": "alert-medium",
        "low": "alert-low",
    }
    _SEV_EMOJI = {
        "critical": "🔴 CRITICAL",
        "high": "🟠 HIGH",
        "medium": "🟡 MEDIUM",
        "low": "🔵 LOW",
    }

    def render_alert(a: dict, expanded: bool = True) -> None:
        sev = a["severity"]
        css = _SEV_CLASS.get(sev, "alert-low")
        badge = _SEV_EMOJI.get(sev, sev.upper())
        new_tag = " 🆕" if a.get("is_new") else " [seen]"
        pos_tag = " ✅ POSITIVE" if a.get("positive") else ""
        market = a.get("market_name") or "All tracked markets"
        body_html = a["body"].replace("\n", "<br>")
        url_html = f'<br><a href="{a["url"]}" target="_blank">Source →</a>' if a.get("url") else ""
        st.markdown(
            f'<div class="{css}">'
            f'<strong>{badge}{new_tag}{pos_tag}</strong><br>'
            f'<em>{market} · {a["triggered_at"]}</em><br><br>'
            f'<strong>{a["title"]}</strong><br><br>'
            f'{body_html}<br><br>'
            f'<strong>Action:</strong> {a["action_required"]}{url_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    if alerts_immediate:
        st.subheader(f"⚡ Immediate — Action Required ({len(alerts_immediate)})")
        for a in alerts_immediate:
            render_alert(a)
    else:
        st.success("No immediate alerts this scan.")

    if alerts_weekly:
        st.subheader(f"📋 Weekly Digest ({len(alerts_weekly)})")
        for a in alerts_weekly:
            with st.expander(
                f"{_SEV_EMOJI.get(a['severity'], a['severity'].upper())}  "
                f"{a['title']}  ·  {a.get('market_name', 'All markets')}",
                expanded=False,
            ):
                render_alert(a)


# ══════════════════════════════════════════════════════════════════════════════
# PROPERTIES TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_props:

    if not props_passed:
        st.info("No properties passed filters this scan.")
    else:
        # ── Summary leaderboard table ─────────────────────────────────────────
        def _cf(v):
            if v is None:
                return None
            return v

        rows = []
        for p in props_passed:
            rows.append({
                "Rk": p["rank"],
                "Address": f"{p['address']}, {p['city']}, {p['state']}",
                "Price": p["price"],
                "Bd": p["bedrooms"],
                "Score": p["composite_score"],
                "Recommendation": p["recommendation"],
                "Cash CF/mo": _cf(p.get("estimated_monthly_cf_cash")),
                "DSCR CF/mo": _cf(p.get("estimated_monthly_cf_dscr")),
                "IRR (cash, 5yr)": p.get("estimated_irr_cash_5yr"),
                "Pool": "✓" if p.get("has_pool") else "",
                "Beach": (
                    f"{p['beach_distance_miles']:.1f}mi"
                    if p.get("beach_distance_miles") is not None else "—"
                ),
                "Flood": p.get("flood_zone", "?"),
                "DOM": p.get("days_on_market"),
            })

        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            column_config={
                "Price": st.column_config.NumberColumn("Price", format="$%d"),
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%.1f"
                ),
                "Cash CF/mo": st.column_config.NumberColumn("Cash CF/mo", format="$%+.0f"),
                "DSCR CF/mo": st.column_config.NumberColumn("DSCR CF/mo", format="$%+.0f"),
                "IRR (cash, 5yr)": st.column_config.NumberColumn("IRR (5yr)", format="%.1f%%",
                                                                   help="5-year IRR on cash purchase"),
                "Recommendation": st.column_config.TextColumn("Action", width="medium"),
            },
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        # ── Per-property drilldown cards ──────────────────────────────────────
        st.divider()
        st.subheader("Property Detail Cards")

        top_n = st.slider("Show top N properties", min_value=3, max_value=len(props_passed),
                          value=min(10, len(props_passed)), step=1)

        for p in props_passed[:top_n]:
            rec_icon = "★★★" if "Strong" in p["recommendation"] else (
                "★★" if "Monitor" in p["recommendation"] else "★"
            )
            label = (
                f"#{p['rank']}  {rec_icon}  {p['address']}, {p['city']}  ·  "
                f"${p['price']:,.0f}  ·  Score {p['composite_score']:.1f}"
            )
            with st.expander(label, expanded=p["rank"] == 1):
                # KPI row
                m1, m2, m3, m4 = st.columns(4)
                cf_cash = p.get("estimated_monthly_cf_cash") or 0
                cf_dscr = p.get("estimated_monthly_cf_dscr") or 0
                irr = p.get("estimated_irr_cash_5yr")
                m1.metric("Cash CF/mo", f"${cf_cash:+,.0f}")
                m2.metric("DSCR CF/mo", f"${cf_dscr:+,.0f}", "30% down @ 7.75%")
                m3.metric("5-yr IRR (cash)", f"{irr*100:.1f}%" if irr else "—",
                          "beats 8% hurdle" if irr and irr >= 0.08 else "trails 8% hurdle")
                m4.metric("EGI (annual)", f"${p.get('estimated_egi_annual') or 0:,.0f}")

                # Property details
                info_cols = st.columns(4)
                info_cols[0].markdown(
                    f"**{p['bedrooms']}bd / {p['bathrooms']}ba**  \n"
                    f"{p['sqft']:,} sqft · Built {p['year_built']}"
                    + (f" (reno {p['renovation_year']})" if p.get("renovation_year") else "")
                )
                beach_str = (
                    f"{p['beach_distance_miles']:.1f}mi"
                    if p.get("beach_distance_miles") is not None else "N/A"
                )
                info_cols[1].markdown(
                    f"Pool: {'✓' if p.get('has_pool') else '✗'}  \n"
                    f"Beach: {beach_str}  \n"
                    f"Flood zone: {p.get('flood_zone', '?')}"
                )
                info_cols[2].markdown(
                    f"Airport: {p.get('airport_code', '?')} ({p.get('airport_drive_min', '?')} min)  \n"
                    f"HOA: {'$' + str(int(p['hoa_monthly'])) + '/mo' if p.get('has_hoa') else 'None'}  \n"
                    f"DOM: {p.get('days_on_market', '?')} days"
                )
                price_red = p.get("price_reduction") or 0
                orig = p.get("original_list_price") or p["price"]
                info_cols[3].markdown(
                    f"Listed: ${orig:,.0f}  \n"
                    f"Reduced: ${price_red:,.0f} ({price_red/orig*100:.1f}%)  \n"
                    f"[View listing →]({p.get('url', '#')})"
                )

                # Scoring factor breakdown
                st.markdown("**Scoring Factors**")
                fdf = pd.DataFrame(p["factors"])
                fdf["score"] = fdf["score"].map(lambda x: f"{x:.0f}/100")
                fdf["weight"] = fdf["weight"].map(lambda x: f"{x:.0%}")
                fdf["contribution"] = fdf["weighted"].map(lambda x: f"{x:.1f} pts")
                st.dataframe(
                    fdf[["name", "score", "weight", "contribution", "note"]].rename(columns={
                        "name": "Factor", "score": "Score", "weight": "Weight",
                        "contribution": "Contribution", "note": "Note",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

        # ── Rejected properties ────────────────────────────────────────────────
        if props_rejected:
            st.divider()
            with st.expander(f"🚫 Filtered Out — {len(props_rejected)} properties"):
                for r in props_rejected:
                    st.markdown(f"**{r['address']}, {r['city']}, {r['state']}** — ${r['price']:,.0f}")
                    for reason in r["failed_reasons"]:
                        st.caption(f"  → {reason}")
                    st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# MARKETS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_markets:

    # ── Score bar chart ───────────────────────────────────────────────────────
    chart_df = pd.DataFrame([
        {"Market": m["name"], "Score": m["composite_score"],
         "State": m["state"], "Regulatory": m["regulatory_status"]}
        for m in markets
    ]).sort_values("Score", ascending=True)

    st.subheader("Market Composite Scores")
    st.bar_chart(chart_df.set_index("Market")["Score"], horizontal=True, height=420)

    # ── Markets table ─────────────────────────────────────────────────────────
    _REG_EMOJI = {
        "stable": "🟢 Stable",
        "evolving_benign": "🟡 Evolving (benign)",
        "evolving_risky": "🟠 Evolving (risky)",
        "restrictive": "🔴 Restrictive",
    }

    mrows = []
    for m in markets:
        delta = m.get("delta")
        mrows.append({
            "Rk": m["rank"],
            "Market": m["name"],
            "State": m["state"],
            "Score": m["composite_score"],
            "Δ": delta,
            "Annual Occ.": m["annual_occupancy_rate"],
            "ADR (3bd)": m["median_adr_3bd"],
            "RevPAN": m["annual_revpan"],
            "Apprecn.": m["home_price_yoy_appreciation"],
            "ADR growth": m["adr_yoy_growth"],
            "Regulatory": _REG_EMOJI.get(m["regulatory_status"], m["regulatory_status"]),
            "Cash Viable": "✓" if m["viable_for_cash_purchase"] else "",
        })

    mdf = pd.DataFrame(mrows)

    st.dataframe(
        mdf,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
            "Δ": st.column_config.NumberColumn("Δ vs prior", format="%+.1f",
                                                help="Change vs prior week composite score"),
            "Annual Occ.": st.column_config.NumberColumn("Ann. Occ.", format="%.0%"),
            "ADR (3bd)": st.column_config.NumberColumn("ADR (3bd)", format="$%d"),
            "RevPAN": st.column_config.NumberColumn("RevPAN", format="$%d",
                                                     help="Revenue per available night (annualized)"),
            "Apprecn.": st.column_config.NumberColumn("Appr.", format="%.1%",
                                                       help="Home price YoY appreciation"),
            "ADR growth": st.column_config.NumberColumn("ADR YoY", format="%.1%"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # ── Per-market factor drilldown ───────────────────────────────────────────
    st.divider()
    st.subheader("Market Factor Breakdown")
    market_name = st.selectbox(
        "Select market",
        [m["name"] for m in markets],
        index=0,
    )

    selected_market = next(m for m in markets if m["name"] == market_name)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Composite Score", f"{selected_market['composite_score']:.1f}/100",
               f"{selected_market['delta']:+.1f} vs prior" if selected_market.get("delta") else None)
    mc2.metric("Regulatory Status", _REG_EMOJI.get(selected_market["regulatory_status"], "?"))
    mc3.metric("Cash Purchase Viable", "Yes ✓" if selected_market["viable_for_cash_purchase"] else "No ✗")

    fdf = pd.DataFrame(selected_market["factors"])
    fdf["score"] = fdf["score"].map(lambda x: f"{x:.0f}/100")
    fdf["weight"] = fdf["weight"].map(lambda x: f"{x:.0%}")
    fdf["contribution"] = fdf["weighted"].map(lambda x: f"{x:.1f} pts")

    st.dataframe(
        fdf[["name", "score", "weight", "contribution", "note"]].rename(columns={
            "name": "Factor", "score": "Score", "weight": "Weight",
            "contribution": "Contribution", "note": "Note",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Regulatory alerts callout
    reg_risky = [m for m in markets if m.get("regulatory_alert")]
    if reg_risky:
        st.warning(
            "⚠️ **Regulatory Watch:**  " +
            "  |  ".join(
                f"{m['name']} ({_REG_EMOJI.get(m['regulatory_status'], m['regulatory_status'])})"
                for m in reg_risky
            )
        )


# ══════════════════════════════════════════════════════════════════════════════
# ANALYZE A PROPERTY TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_analyze:

    st.subheader("🔍 Instant Property Analysis")
    st.markdown(
        "Paste any Zillow listing URL below and get an instant scoring, "
        "financial pro forma, and investment recommendation — the same analysis "
        "the weekly scan runs on every property."
    )

    col_url, col_key = st.columns([3, 1])
    with col_url:
        zillow_url = st.text_input(
            "Zillow listing URL",
            placeholder="https://www.zillow.com/homedetails/123-Ocean-Dr-Emerald-Isle-NC-28594/12345678_zpid/",
        )
    with col_key:
        api_key_input = st.text_input(
            "RapidAPI key",
            type="password",
            value=os.getenv("RAPIDAPI_KEY", ""),
            help="Your private-zillow RapidAPI key. Add RAPIDAPI_KEY to .env to pre-fill this.",
        )

    # Down payment override
    st.markdown("**Financing assumptions** (optional overrides)")
    fc1, fc2, fc3 = st.columns(3)
    down_pct   = fc1.slider("Down payment %", 20, 100, 30, step=5)
    dscr_rate  = fc2.slider("DSCR rate %", 6.0, 10.0, 7.75, step=0.25)
    hold_years = fc3.slider("Hold period (years)", 3, 10, 5)

    analyze_btn = st.button("▶ Analyze this property", type="primary", use_container_width=True)

    if analyze_btn:
        if not zillow_url:
            st.warning("Paste a Zillow URL above first.")
        elif not api_key_input:
            st.warning(
                "Enter your RapidAPI key. "
                "Get one free at [rapidapi.com](https://rapidapi.com/apimaker/api/private-zillow)."
            )
        else:
            with st.spinner("Fetching listing from Zillow…"):
                from real_estate_agent.properties.sources.zillow_url import lookup_by_url
                listing, error = lookup_by_url(zillow_url, api_key_input)

            if error:
                st.error(f"**Could not fetch listing:** {error}")
            elif listing is None:
                st.error("No data returned. Check the URL is a valid Zillow listing page.")
            else:
                # ── Property header ───────────────────────────────────────────
                st.success(f"✓ Fetched: **{listing.address}, {listing.city}, {listing.state}**")
                st.divider()

                # ── Hard filter check ─────────────────────────────────────────
                from real_estate_agent.scoring.markets import MARKETS_BY_ID
                from real_estate_agent.properties.filters import apply_filters
                from real_estate_agent.properties.enrichment import enrich
                from real_estate_agent.properties.scorer import score_property, recommendation, WEIGHTS
                from real_estate_agent.scoring.scorer import score_market
                from real_estate_agent.financial.models import (
                    ScenarioInputs, FinancingInputs, FinancingType,
                )
                from real_estate_agent.financial.proforma import generate_proforma
                from real_estate_agent.financial.metrics import SELLING_COST_PCT

                snapshot = MARKETS_BY_ID.get(listing.market_id)
                market_name = snapshot.name if snapshot else "Outside tracked markets"

                # Show basic facts
                f1, f2, f3, f4, f5 = st.columns(5)
                f1.metric("Price", f"${listing.price:,.0f}")
                f2.metric("Beds / Baths", f"{listing.bedrooms}bd / {listing.bathrooms}ba")
                f3.metric("Sqft / Year", f"{listing.sqft:,} / {listing.year_built}")
                f4.metric("Market", market_name)
                f5.metric(
                    "Beach",
                    f"{listing.beach_distance_miles:.1f}mi" if listing.beach_distance_miles is not None else "N/A",
                )

                st.markdown(
                    f"Pool: {'✓' if listing.has_pool else '✗'}  ·  "
                    f"HOA: {'$' + str(int(listing.hoa_monthly)) + '/mo' if listing.has_hoa else 'None'}  ·  "
                    f"Flood zone: {listing.flood_zone}  ·  "
                    f"Airport: {listing.airport_code} ({listing.airport_drive_min} min)  ·  "
                    f"DOM: {listing.days_on_market} days"
                )

                if snapshot:
                    fr = apply_filters(listing, snapshot)
                    if not fr.passed:
                        st.error("🚫 **This property fails your hard filters:**")
                        for reason in fr.failed_reasons:
                            st.markdown(f"  - {reason}")
                        st.markdown("The financial analysis below is shown for reference only.")
                    else:
                        st.success("✅ Passes all hard filters")
                else:
                    st.warning(
                        f"⚠️ '{listing.city}' is outside your 13 tracked markets. "
                        "Financial model uses Crystal Coast averages as a proxy — treat with caution."
                    )

                # ── Financial model ────────────────────────────────────────────
                st.divider()
                st.subheader("💰 Financial Analysis")

                with st.spinner("Running financial model…"):
                    if snapshot:
                        enrich(listing, snapshot, personal_use_weeks=4)
                    else:
                        # Fallback: use Crystal Coast as proxy market
                        proxy = MARKETS_BY_ID["nc_crystal_coast_carteret"]
                        enrich(listing, proxy, personal_use_weeks=4)

                cf_cash = listing.estimated_monthly_cf_cash or 0
                cf_dscr = listing.estimated_monthly_cf_dscr or 0
                irr     = listing.estimated_irr_cash_5yr

                m1, m2, m3, m4 = st.columns(4)
                m1.metric(
                    "Cash CF / mo",
                    f"${cf_cash:+,.0f}",
                    "within -$1k floor" if cf_cash >= -1000 else "⚠ below -$1k floor",
                    delta_color="normal" if cf_cash >= -1000 else "inverse",
                )
                m2.metric(
                    f"DSCR CF / mo",
                    f"${cf_dscr:+,.0f}",
                    f"30% down @ 7.75%",
                    delta_color="normal" if cf_dscr >= -1000 else "inverse",
                )
                m3.metric(
                    "5-yr IRR (cash)",
                    f"{irr*100:.1f}%" if irr else "—",
                    "beats 8% hurdle" if irr and irr >= 0.08 else "trails 8% hurdle",
                    delta_color="normal" if irr and irr >= 0.08 else "inverse",
                )
                m4.metric("Annual EGI", f"${listing.estimated_egi_annual or 0:,.0f}")

                # ── Detailed pro formas ────────────────────────────────────────
                with st.expander("📄 Full Pro Forma — Cash Purchase"):
                    from real_estate_agent.financial.models import (
                        PropertyInputs, MarketInputs, InsuranceInputs,
                        OperatingExpenseInputs, FinancingType, MarketType,
                    )
                    from real_estate_agent.financial.metrics import calculate_all_metrics
                    from real_estate_agent.properties.enrichment import (
                        _market_inputs, _property_inputs, _insurance,
                    )

                    used_snap = snapshot or MARKETS_BY_ID["nc_crystal_coast_carteret"]
                    market_in = _market_inputs(used_snap, listing)
                    prop_in   = _property_inputs(listing, used_snap)
                    ins       = _insurance(used_snap, listing)
                    ops       = OperatingExpenseInputs()

                    cash_inputs = ScenarioInputs(
                        property=prop_in, market=market_in,
                        financing=FinancingInputs(
                            financing_type=FinancingType.CASH,
                            down_payment=listing.price,
                            interest_rate=0.0, loan_term_years=0,
                        ),
                        insurance=ins, operating=ops,
                        annual_personal_use_weeks=4, hold_period_years=hold_years,
                    )
                    cm = calculate_all_metrics(cash_inputs)
                    exp = cm["expenses"]

                    rc1, rc2 = st.columns(2)
                    with rc1:
                        st.markdown("**Revenue**")
                        st.markdown(f"Annual EGI: **${cm['revenue']['effective_gross_income']:,.0f}**")
                        st.markdown(f"NOI: **${cm['noi']:,.0f}**")
                    with rc2:
                        st.markdown("**Key Metrics**")
                        st.markdown(f"Annual CF: **${cm['annual_cash_flow']:+,.0f}**")
                        st.markdown(f"Monthly CF: **${cm['monthly_cash_flow']:+,.0f}**")
                        st.markdown(f"Cash-on-Cash: **{cm['cash_on_cash_return']*100:.1f}%**")
                        st.markdown(f"5-yr IRR: **{cm['irr']*100:.1f}%**" if cm['irr'] else "5-yr IRR: —")
                        st.markdown(f"18-mo net position: **${cm['net_position_18mo']:+,.0f}**")

                    st.markdown("**Expense breakdown**")
                    exp_df = pd.DataFrame([
                        {"Item": "Property tax",     "Annual": exp["property_tax"]},
                        {"Item": "Insurance (total)","Annual": exp["insurance_total"]},
                        {"Item": "HOA",              "Annual": exp["hoa"]},
                        {"Item": "Utilities",        "Annual": exp["utilities"]},
                        {"Item": "Landscaping",      "Annual": exp["landscaping"]},
                        {"Item": "Cleaning/turnover","Annual": exp["cleaning_turnover"]},
                        {"Item": "Maintenance reserve", "Annual": exp["maintenance_reserve"]},
                        {"Item": "CapEx reserve",    "Annual": exp["capex_reserve"]},
                        {"Item": "STR licensing",    "Annual": exp["str_licensing"]},
                        {"Item": "Accounting",       "Annual": exp["accounting"]},
                    ])
                    st.dataframe(
                        exp_df,
                        column_config={"Annual": st.column_config.NumberColumn("Annual", format="$%d")},
                        use_container_width=True, hide_index=True,
                    )

                with st.expander(f"📄 Full Pro Forma — DSCR Loan ({down_pct}% down @ {dscr_rate}%)"):
                    down_amt = listing.price * (down_pct / 100)
                    dscr_inputs = ScenarioInputs(
                        property=prop_in, market=market_in,
                        financing=FinancingInputs(
                            financing_type=FinancingType.DSCR,
                            down_payment=down_amt,
                            interest_rate=dscr_rate / 100,
                            loan_term_years=30,
                        ),
                        insurance=ins, operating=ops,
                        annual_personal_use_weeks=4, hold_period_years=hold_years,
                    )
                    dm = calculate_all_metrics(dscr_inputs)

                    dr1, dr2 = st.columns(2)
                    with dr1:
                        st.markdown("**Financing**")
                        st.markdown(f"Down payment: **${down_amt:,.0f}** ({down_pct}%)")
                        st.markdown(f"Loan: **${listing.price - down_amt:,.0f}** @ {dscr_rate}%")
                        st.markdown(f"Monthly P&I: **${dm['expenses']['mortgage_monthly']:,.0f}**")
                        st.markdown(f"Cash to close: **${dm['cash_to_close']:,.0f}**")
                    with dr2:
                        st.markdown("**Key Metrics**")
                        st.markdown(f"Monthly CF: **${dm['monthly_cash_flow']:+,.0f}**")
                        dscr_val = dm['dscr']
                        dscr_label = f"{dscr_val:.2f}x" if dscr_val != float('inf') else "N/A"
                        pass_fail = "✅ PASSES" if dm['dscr_passes_lender_min'] else "❌ FAILS lender min 1.1x"
                        st.markdown(f"DSCR: **{dscr_label}** — {pass_fail}")
                        st.markdown(f"5-yr IRR: **{dm['irr']*100:.1f}%**" if dm['irr'] else "5-yr IRR: —")
                        hurdle_label = f"${dm['hurdle_fv_5yr']:,.0f} (gain ${dm['hurdle_gain_5yr']:,.0f})"
                        st.markdown(f"8% hurdle ({hold_years}yr): **{hurdle_label}**")

                # ── Property score ─────────────────────────────────────────────
                if snapshot:
                    st.divider()
                    st.subheader("📊 Investment Score")
                    ms = score_market(snapshot)
                    factors = score_property(listing, ms)
                    composite = sum(f.weighted for f in factors)
                    rec = recommendation(composite)

                    sc1, sc2 = st.columns([1, 3])
                    sc1.metric("Score", f"{composite:.1f}/100", rec)

                    fdf2 = pd.DataFrame([{
                        "Factor": f.name,
                        "Score": f"{f.score:.0f}/100",
                        "Weight": f"{f.weight:.0%}",
                        "Contribution": f"{f.weighted:.1f} pts",
                        "Note": f.note,
                    } for f in factors])
                    sc2.dataframe(fdf2, use_container_width=True, hide_index=True)

                # ── Listing link ───────────────────────────────────────────────
                if listing.url and listing.url.startswith("http"):
                    st.markdown(f"[View on Zillow →]({listing.url})")
