from __future__ import annotations

from .models import ScenarioInputs, FinancingType
from .metrics import calculate_all_metrics, MONTHLY_CF_FLOOR, LENDER_MIN_DSCR, SELLING_COST_PCT


def _c(v: float, sign: bool = False) -> str:
    prefix = "+" if sign and v >= 0 else ""
    if v < 0:
        return f"-${abs(v):>10,.0f}"
    return f"{prefix}${v:>10,.0f}"


def _pct(v: float | None) -> str:
    if v is None:
        return "     N/A"
    return f"{v * 100:>7.1f}%"


def _flag(condition: bool, ok_label: str = "OK", warn_label: str = "WARN") -> str:
    return f"[{'OK  ' if not condition else 'WARN'}] {ok_label if not condition else warn_label}"


def generate_proforma(inputs: ScenarioInputs, scenario_name: str = "Scenario") -> dict:
    return {
        "scenario_name": scenario_name,
        "inputs": inputs,
        "metrics": calculate_all_metrics(inputs),
    }


def print_proforma(result: dict) -> None:
    name = result["scenario_name"]
    inp: ScenarioInputs = result["inputs"]
    m = result["metrics"]
    rev = m["revenue"]
    exp = m["expenses"]
    sens = m["sensitivity"]
    p = inp.property
    f = inp.financing

    W = 68

    def hr(char="─"):
        print(f"  {char * (W - 2)}")

    print(f"\n{'═' * W}")
    print(f"  PRO FORMA  ·  {name}")
    print(f"{'═' * W}")

    print(f"\n  Purchase Price:         {_c(p.purchase_price)}")
    print(f"  Down Payment:           {_c(f.down_payment)}  ({f.down_payment / p.purchase_price * 100:.0f}% LTV inverse)")
    print(f"  Loan Amount:            {_c(p.purchase_price - f.down_payment)}")
    if f.financing_type != FinancingType.CASH:
        print(f"  Interest Rate:          {_pct(f.interest_rate)}   ({f.loan_term_years}-yr {f.financing_type.value.upper()})")
        print(f"  Monthly P&I:            {_c(exp['mortgage_monthly'])}/mo")
    print(f"  Cash to Close (est.):   {_c(m['cash_to_close'])}")

    print(f"\n{'─' * W}")
    print(f"  RENTAL REVENUE")
    hr()
    print(f"  Peak (Jun–Aug, {rev['peak_days_available']:2d} days avail):  {_c(rev['peak_revenue'])}")
    print(f"  Shoulder ({rev['shoulder_days_available']:3d} days avail):          {_c(rev['shoulder_revenue'])}")
    print(f"  Off-season ({rev['offseason_days_available']:3d} days avail):        {_c(rev['offseason_revenue'])}")
    print(f"  {'─' * 50}")
    print(f"  Gross Revenue:                          {_c(rev['gross_revenue'])}")
    print(f"  Less PM Commission ({_pct(inp.market.pm_commission_rate).strip()}):      -{_c(rev['pm_commission']).strip()}")
    print(f"  Less Platform Fees ({_pct(inp.market.platform_fee_rate).strip()}):       -{_c(rev['platform_fees']).strip()}")
    print(f"  {'─' * 50}")
    print(f"  Effective Gross Income (EGI):           {_c(rev['effective_gross_income'])}")

    print(f"\n{'─' * W}")
    print(f"  ANNUAL EXPENSES")
    hr()
    if f.financing_type != FinancingType.CASH:
        print(f"  Mortgage (P&I):                         {_c(exp['mortgage_annual'])}")
    print(f"  Property Tax ({_pct(inp.market.property_tax_rate).strip()}):             {_c(exp['property_tax'])}")
    print(f"  Insurance (home + STR + wind + flood):  {_c(exp['insurance_total'])}")
    if p.has_hoa and exp["hoa"] > 0:
        print(f"  HOA:                                    {_c(exp['hoa'])}")
    print(f"  Utilities:                              {_c(exp['utilities'])}")
    print(f"  Landscaping:                            {_c(exp['landscaping'])}")
    print(f"  Cleaning / Turnover (net):              {_c(exp['cleaning_turnover'])}")
    print(f"  Accounting / Legal:                     {_c(exp['accounting'])}")
    print(f"  STR Licensing:                          {_c(exp['str_licensing'])}")
    maint_pct_lbl = f"{exp['maintenance_reserve_pct']*100:.1f}%"
    capex_pct_lbl = f"{exp['capex_reserve_pct']*100:.1f}%"
    print(f"  Maintenance Reserve ({maint_pct_lbl}, age {p.property_age_years}yr):  {_c(exp['maintenance_reserve'])}")
    print(f"  CapEx Reserve ({capex_pct_lbl}):                {_c(exp['capex_reserve'])}")
    print(f"  {'─' * 50}")
    print(f"  Total Annual Expenses:                  {_c(exp['total_annual'])}")

    print(f"\n{'─' * W}")
    print(f"  KEY METRICS")
    hr()
    print(f"  Net Operating Income (NOI):             {_c(m['noi'])}")
    print(f"  Annual Cash Flow:                       {_c(m['annual_cash_flow'], sign=True)}")
    print(f"  Monthly Cash Flow:                      {_c(m['monthly_cash_flow'], sign=True)}/mo")
    print(f"  Cash-on-Cash Return:                    {_pct(m['cash_on_cash_return'])}")

    if f.financing_type != FinancingType.CASH:
        dscr_ok = not m["dscr_passes_lender_min"]
        dscr_label = f"{m['dscr']:.2f}x  ({'PASSES' if m['dscr_passes_lender_min'] else f'FAILS — lender min {LENDER_MIN_DSCR}x'})"
        print(f"  DSCR Ratio:                             {dscr_label}")

    be = m["breakeven"]
    if be["pct_of_stated_occupancy"] is not None:
        be_flag = "ACHIEVABLE" if be["pct_of_stated_occupancy"] <= 1.0 else "UNACHIEVABLE at stated rates"
        print(f"  Break-Even Occupancy:                   {_pct(be['breakeven_blended_occupancy'])} blended  ({be_flag})")
        print(f"    (requires {be['pct_of_stated_occupancy']*100:.0f}% of stated seasonal rates)")

    print(f"  18-Month Cumulative CF:                 {_c(m['cumulative_18mo_cash_flow'], sign=True)}")
    if m["irr"] is not None:
        print(f"  {inp.hold_period_years}-Year IRR (incl. appreciation + sale):  {_pct(m['irr'])}")
    print(f"  Net Sale Proceeds (Year {inp.hold_period_years}, {SELLING_COST_PCT*100:.1f}% cost): {_c(m['net_sale_proceeds_at_exit'])}")
    print(f"  18-Month Appreciation (est.):           {_c(m['appreciation_18mo'], sign=True)}")
    print(f"  18-Month Net Position (CF+Appr.):       {_c(m['net_position_18mo'], sign=True)}")

    print(f"\n{'─' * W}")
    print(f"  SENSITIVITY ANALYSIS")
    hr()
    if sens["peak_adr_needed_for_floor"] is not None:
        scale = sens["adr_scale_needed_for_floor"]
        if scale is not None and scale > 0:
            print(f"  Peak ADR needed for -$1k/mo floor:     ${sens['peak_adr_needed_for_floor']:,.0f}  (currently ${inp.market.peak_adr:,.0f}, need {(scale-1)*100:+.0f}%)")
        else:
            print(f"  ADR sensitivity: already meets floor at stated rates")
    if sens["occupancy_scale_needed_for_floor"] is not None:
        occ_scale = sens["occupancy_scale_needed_for_floor"]
        label = f"need {(occ_scale - 1) * 100:+.0f}% occupancy lift" if occ_scale > 1 else f"currently {(1 - occ_scale) * 100:.0f}% headroom"
        print(f"  Occupancy scale needed for -$1k/mo:    {occ_scale * 100:.0f}% of stated  ({label})")
    print(f"  Stress test (-15% ADR & occupancy):")
    print(f"    Annual CF:                            {_c(sens['stressed_annual_cf_minus15pct'], sign=True)}")
    print(f"    Monthly CF:                           {_c(sens['stressed_monthly_cf_minus15pct'], sign=True)}/mo")

    print(f"\n{'─' * W}")
    print(f"  TOTAL RETURN vs. 8% EQUITY MARKET HURDLE ({inp.hold_period_years}-yr)")
    hr()
    hurdle_rate_pct = m["hurdle_rate"] * 100
    print(f"  Capital deployed (cash to close):       {_c(m['cash_to_close'])}")
    print(f"  Equity market at {hurdle_rate_pct:.0f}%/yr (S&P equiv.):  {_c(m['hurdle_fv_5yr'])}  (gain: {_c(m['hurdle_gain_5yr'], sign=True).strip()})")
    prop_final_equity = m["equity_projections"][-1]["equity"] if m["equity_projections"] else 0
    total_cf = sum(yr["year_cash_flow"] for yr in m["equity_projections"])
    prop_total_return = prop_final_equity - (inp.property.purchase_price - inp.financing.down_payment) + total_cf
    if m["irr"] is not None:
        beats_hurdle = m["irr"] >= m["hurdle_rate"]
        print(f"  Property IRR ({inp.hold_period_years}-yr):                  {_pct(m['irr'])}  ({'BEATS' if beats_hurdle else 'TRAILS'} {hurdle_rate_pct:.0f}% hurdle)")
    print(f"  Property equity at Year {inp.hold_period_years}:              {_c(prop_final_equity)}")
    print(f"  Cumulative rental CF ({inp.hold_period_years} yr):           {_c(total_cf, sign=True)}")

    print(f"\n{'─' * W}")
    print(f"  {inp.hold_period_years}-YEAR EQUITY PROJECTION  (appreciation @ {inp.market.annual_appreciation_rate*100:.1f}%/yr, ADR @ +{inp.market.annual_adr_growth_rate*100:.1f}%/yr)")
    hr()
    print(f"  {'Yr':<4}  {'Property Value':<17}  {'Remaining Loan':<17}  {'Equity':<14}  {'Ann. CF'}")
    print(f"  {'─'*64}")
    for yr in m["equity_projections"]:
        print(f"  {yr['year']:<4}  ${yr['property_value']:>14,.0f}  ${yr['remaining_loan']:>14,.0f}  ${yr['equity']:>12,.0f}  {_c(yr['year_cash_flow'], sign=True).strip()}")

    print(f"\n{'─' * W}")
    print(f"  FLAGS")
    hr()
    cf_breach = m["cf_floor_flag"]
    print(f"  {'[WARN]' if cf_breach else '[OK  ]'} Monthly CF {'below' if cf_breach else 'within'} -$1,000/mo floor  (actual: {_c(m['monthly_cash_flow'], sign=True).strip()}/mo)")
    if f.financing_type != FinancingType.CASH:
        dscr_fail = not m["dscr_passes_lender_min"]
        print(f"  {'[WARN]' if dscr_fail else '[OK  ]'} DSCR {m['dscr']:.2f}x {'— lender will likely require reserves or deny' if dscr_fail else '— meets lender minimum'}")
    net_pos = m["net_position_18mo"]
    print(f"  {'[WARN]' if m['exit_trigger_flag'] else '[OK  ]'} 18-mo net position (CF + appreciation): {_c(net_pos, sign=True).strip()}  {'— EXIT TRIGGER ACTIVE' if m['exit_trigger_flag'] else ''}")
    print(f"\n{'═' * W}\n")


def compare_scenarios(results: list[dict]) -> None:
    """Prints a side-by-side summary table of multiple scenarios."""
    W = 80
    print(f"\n{'═' * W}")
    print(f"  SCENARIO COMPARISON")
    print(f"{'═' * W}")

    labels = [r["scenario_name"][:28] for r in results]
    col_w = 18

    def row(label: str, values: list[str]):
        print(f"  {label:<32}  " + "  ".join(f"{v:>{col_w}}" for v in values))

    print(f"  {'Metric':<32}  " + "  ".join(f"{l:>{col_w}}" for l in labels))
    print(f"  {'─' * 32}  " + "  ".join("─" * col_w for _ in labels))

    def metric_row(label: str, fn):
        vals = []
        for r in results:
            try:
                vals.append(fn(r))
            except Exception:
                vals.append("N/A")
        row(label, vals)

    metric_row("Cash to Close", lambda r: f"${r['metrics']['cash_to_close']:,.0f}")
    metric_row("Annual EGI", lambda r: f"${r['metrics']['revenue']['effective_gross_income']:,.0f}")
    metric_row("Total Expenses", lambda r: f"${r['metrics']['expenses']['total_annual']:,.0f}")
    metric_row("Annual Cash Flow", lambda r: f"{'+' if r['metrics']['annual_cash_flow'] >= 0 else ''}${r['metrics']['annual_cash_flow']:,.0f}")
    metric_row("Monthly Cash Flow", lambda r: f"{'+' if r['metrics']['monthly_cash_flow'] >= 0 else ''}${r['metrics']['monthly_cash_flow']:,.0f}/mo")
    metric_row("Cash-on-Cash Return", lambda r: f"{r['metrics']['cash_on_cash_return']*100:.1f}%")
    metric_row("DSCR", lambda r: f"{r['metrics']['dscr']:.2f}x" if r['metrics']['dscr'] != float('inf') else "N/A (cash)")
    metric_row("Break-Even Occ.", lambda r: f"{(r['metrics']['breakeven']['breakeven_blended_occupancy'] or 0)*100:.1f}%")
    metric_row("18-Mo Net Position", lambda r: f"${r['metrics']['net_position_18mo']:,.0f}")
    metric_row(f"IRR ({results[0]['inputs'].hold_period_years}-yr)", lambda r: f"{r['metrics']['irr']*100:.1f}%" if r['metrics']['irr'] else "N/A")
    metric_row(f"Hurdle ({results[0]['inputs'].hold_period_years}-yr @8%)", lambda r: f"${r['metrics']['hurdle_fv_5yr']:,.0f}")
    metric_row("CF Floor Breach?", lambda r: "YES ⚠" if r['metrics']['cf_floor_flag'] else "No")
    metric_row("Exit Trigger?", lambda r: "YES ⚠" if r['metrics']['exit_trigger_flag'] else "No")

    print(f"{'═' * W}\n")
