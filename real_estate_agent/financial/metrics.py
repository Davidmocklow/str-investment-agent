from __future__ import annotations

from .models import ScenarioInputs
from .revenue import effective_gross_income, PEAK_DAYS, SHOULDER_DAYS, OFFSEASON_DAYS
from .expenses import annual_expenses, operating_expenses_ex_debt
from .financing import loan_amount, total_cash_to_close, amortization_by_year

# Owner's stated tolerance: -$1,000/mo cash flow before triggering concern
MONTHLY_CF_FLOOR = -1_000.0
# Lender minimum DSCR for approval
LENDER_MIN_DSCR = 1.10
# Selling cost assumption (agent + transfer + title)
SELLING_COST_PCT = 0.075


def _irr(cash_flows: list[float], guess: float = 0.08) -> float | None:
    """Newton-Raphson IRR. Returns None if it fails to converge."""
    rate = guess
    for _ in range(500):
        npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
        if abs(dnpv) < 1e-12:
            return None
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < 1e-9:
            return new_rate
        rate = new_rate
    return None


def _breakeven_occupancy(egi: float, total_expenses: float, market) -> dict:
    """
    Finds the uniform occupancy scale factor that makes annual cash flow = 0.
    Returns the required blended occupancy rate and % of stated rates needed.
    """
    if egi == 0:
        return {"breakeven_blended_occupancy": None, "pct_of_stated_occupancy": None}

    scale = total_expenses / egi  # >1 means never breaks even at stated rates
    blended_stated = (
        market.peak_occupancy * PEAK_DAYS +
        market.shoulder_occupancy * SHOULDER_DAYS +
        market.offseason_occupancy * OFFSEASON_DAYS
    ) / 365
    required_blended = blended_stated * scale

    return {
        "breakeven_blended_occupancy": required_blended,
        "pct_of_stated_occupancy": scale,
    }


def _sensitivity(inputs: ScenarioInputs, exp: dict) -> dict:
    """
    Calculates what ADR or occupancy is needed to hit the $1k/mo cash flow floor.
    Also stress-tests a 15% ADR + occupancy drop.
    """
    total_exp = exp["total_annual"]
    target_egi = total_exp + (MONTHLY_CF_FLOOR * 12)  # EGI needed for -$1k/mo

    # ADR sensitivity: scale ADR uniformly to hit target EGI
    base_rev = effective_gross_income(inputs.market, inputs.annual_personal_use_weeks)
    base_egi = base_rev["effective_gross_income"]
    base_gross = base_rev["gross_revenue"]

    if base_gross > 0:
        fee_retention = base_egi / base_gross  # fraction kept after PM + platform
        gross_needed = target_egi / fee_retention if fee_retention > 0 else None
        current_gross = base_gross
        adr_scale_needed = (gross_needed / current_gross) if gross_needed and current_gross > 0 else None
        adr_peak_needed = inputs.market.peak_adr * adr_scale_needed if adr_scale_needed else None
    else:
        adr_scale_needed = None
        adr_peak_needed = None

    # Occupancy sensitivity: scale occupancy uniformly
    occ_scale_needed = (target_egi / base_egi) if base_egi > 0 else None

    # Stress test: -15% ADR and -15% occupancy simultaneously
    from .models import MarketInputs
    stressed_market = MarketInputs(
        peak_adr=inputs.market.peak_adr * 0.85,
        shoulder_adr=inputs.market.shoulder_adr * 0.85,
        offseason_adr=inputs.market.offseason_adr * 0.85,
        peak_occupancy=inputs.market.peak_occupancy * 0.85,
        shoulder_occupancy=inputs.market.shoulder_occupancy * 0.85,
        offseason_occupancy=inputs.market.offseason_occupancy * 0.85,
        pm_commission_rate=inputs.market.pm_commission_rate,
        platform_fee_rate=inputs.market.platform_fee_rate,
        occupancy_tax_rate=inputs.market.occupancy_tax_rate,
        property_tax_rate=inputs.market.property_tax_rate,
        annual_appreciation_rate=inputs.market.annual_appreciation_rate,
        annual_adr_growth_rate=inputs.market.annual_adr_growth_rate,
    )
    stressed_rev = effective_gross_income(stressed_market, inputs.annual_personal_use_weeks)
    stressed_cf_annual = stressed_rev["effective_gross_income"] - total_exp

    return {
        "adr_scale_needed_for_floor": adr_scale_needed,
        "peak_adr_needed_for_floor": adr_peak_needed,
        "occupancy_scale_needed_for_floor": occ_scale_needed,
        "stressed_annual_cf_minus15pct": stressed_cf_annual,
        "stressed_monthly_cf_minus15pct": stressed_cf_annual / 12,
    }


def calculate_all_metrics(inputs: ScenarioInputs) -> dict:
    rev = effective_gross_income(inputs.market, inputs.annual_personal_use_weeks)
    exp = annual_expenses(inputs)

    egi = rev["effective_gross_income"]
    total_exp = exp["total_annual"]
    ops_ex_debt = operating_expenses_ex_debt(exp)

    # Core cash flow
    noi = egi - ops_ex_debt          # before debt service (used for DSCR)
    annual_cf = egi - total_exp
    monthly_cf = annual_cf / 12

    # Cash-on-cash return
    ctc = total_cash_to_close(
        inputs.property.purchase_price,
        inputs.financing.down_payment,
        inputs.financing.financing_type,
    )
    coc = annual_cf / ctc if ctc > 0 else 0.0

    # DSCR
    debt_service = exp["mortgage_annual"]
    dscr = noi / debt_service if debt_service > 0 else float("inf")
    dscr_passes = dscr >= LENDER_MIN_DSCR

    # Break-even occupancy
    be = _breakeven_occupancy(egi, total_exp, inputs.market)

    # 18-month cumulative cash flow + unrealized appreciation
    cumulative_18mo = monthly_cf * 18
    appreciation_18mo = inputs.property.purchase_price * (
        (1 + inputs.market.annual_appreciation_rate) ** 1.5 - 1
    )
    net_position_18mo = cumulative_18mo + appreciation_18mo

    # Multi-year equity projection with growing ADR
    loan = loan_amount(inputs.property.purchase_price, inputs.financing.down_payment)
    amort = amortization_by_year(loan, inputs.financing.interest_rate, inputs.financing.loan_term_years, inputs.hold_period_years)

    equity_projections = []
    prop_value = inputs.property.purchase_price
    adr_multiplier = 1.0

    for yr_data in amort:
        year = yr_data["year"]
        prop_value *= (1 + inputs.market.annual_appreciation_rate)
        adr_multiplier *= (1 + inputs.market.annual_adr_growth_rate)
        remaining_loan = yr_data["remaining_balance"]
        equity = prop_value - remaining_loan

        # Year-specific cash flow (ADR grows annually, expenses flat for conservatism)
        from .models import MarketInputs as MI
        yr_market = MI(
            peak_adr=inputs.market.peak_adr * adr_multiplier,
            shoulder_adr=inputs.market.shoulder_adr * adr_multiplier,
            offseason_adr=inputs.market.offseason_adr * adr_multiplier,
            peak_occupancy=inputs.market.peak_occupancy,
            shoulder_occupancy=inputs.market.shoulder_occupancy,
            offseason_occupancy=inputs.market.offseason_occupancy,
            pm_commission_rate=inputs.market.pm_commission_rate,
            platform_fee_rate=inputs.market.platform_fee_rate,
            occupancy_tax_rate=inputs.market.occupancy_tax_rate,
            property_tax_rate=inputs.market.property_tax_rate,
            annual_appreciation_rate=inputs.market.annual_appreciation_rate,
            annual_adr_growth_rate=inputs.market.annual_adr_growth_rate,
        )
        yr_rev = effective_gross_income(yr_market, inputs.annual_personal_use_weeks)
        yr_cf = yr_rev["effective_gross_income"] - total_exp

        equity_projections.append({
            "year": year,
            "property_value": prop_value,
            "remaining_loan": remaining_loan,
            "equity": equity,
            "equity_vs_initial": equity - inputs.financing.down_payment,
            "year_cash_flow": yr_cf,
            "year_egi": yr_rev["effective_gross_income"],
        })

    # IRR: Year 0 = -cash_to_close; Years 1..N = annual_cf; Year N += net sale proceeds
    final_value = equity_projections[-1]["property_value"] if equity_projections else inputs.property.purchase_price
    final_loan = equity_projections[-1]["remaining_loan"] if equity_projections else loan
    net_sale = final_value * (1 - SELLING_COST_PCT) - final_loan

    irr_flows = [-ctc]
    for i, yr in enumerate(equity_projections):
        cf = yr["year_cash_flow"]
        if i == len(equity_projections) - 1:
            cf += net_sale
        irr_flows.append(cf)

    irr = _irr(irr_flows)

    # Sensitivity analysis
    sensitivity = _sensitivity(inputs, exp)

    # Flags
    # Exit: cumulative 18-mo CF losses not covered by unrealized appreciation
    exit_flag = net_position_18mo < 0
    cf_floor_flag = monthly_cf < MONTHLY_CF_FLOOR

    # Hurdle rate: what the down payment would grow to at 8% equity market return
    HURDLE_RATE = 0.08
    hurdle_fv_5yr = ctc * (1 + HURDLE_RATE) ** inputs.hold_period_years
    hurdle_gain_5yr = hurdle_fv_5yr - ctc

    return {
        "revenue": rev,
        "expenses": exp,
        "noi": noi,
        "annual_cash_flow": annual_cf,
        "monthly_cash_flow": monthly_cf,
        "cash_on_cash_return": coc,
        "dscr": dscr,
        "dscr_passes_lender_min": dscr_passes,
        "breakeven": be,
        "cumulative_18mo_cash_flow": cumulative_18mo,
        "appreciation_18mo": appreciation_18mo,
        "net_position_18mo": net_position_18mo,
        "equity_projections": equity_projections,
        "irr": irr,
        "net_sale_proceeds_at_exit": net_sale,
        "cash_to_close": ctc,
        "sensitivity": sensitivity,
        "exit_trigger_flag": exit_flag,
        "cf_floor_flag": cf_floor_flag,
        "hurdle_rate": HURDLE_RATE,
        "hurdle_fv_5yr": hurdle_fv_5yr,
        "hurdle_gain_5yr": hurdle_gain_5yr,
    }
