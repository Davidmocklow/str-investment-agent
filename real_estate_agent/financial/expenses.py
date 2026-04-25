from .models import ScenarioInputs
from .financing import monthly_payment, loan_amount


def _age_based_reserve_rates(age_years: int) -> tuple:
    """
    Returns (maintenance_pct, capex_pct) scaled by property age.
    Newer properties have lower reserve requirements; older ones front-load CapEx risk.
    """
    if age_years < 5:
        return 0.015, 0.010
    elif age_years < 10:
        return 0.020, 0.013
    elif age_years < 15:
        return 0.027, 0.017
    elif age_years < 20:
        return 0.035, 0.022
    else:
        return 0.040, 0.025


def annual_expenses(inputs: ScenarioInputs) -> dict:
    p = inputs.property
    m = inputs.market
    f = inputs.financing
    ins = inputs.insurance
    ops = inputs.operating

    # Debt service
    loan = loan_amount(p.purchase_price, f.down_payment)
    monthly_pi = monthly_payment(loan, f.interest_rate, f.loan_term_years)
    annual_mortgage = monthly_pi * 12

    # Taxes and insurance
    annual_property_tax = p.purchase_price * m.property_tax_rate
    annual_insurance = (
        ins.homeowners_monthly + ins.str_liability_monthly +
        ins.windstorm_monthly + ins.flood_monthly
    ) * 12

    # HOA
    annual_hoa = p.hoa_monthly * 12 if p.has_hoa else 0.0

    # Operating
    annual_utilities = ops.utilities_monthly * 12
    annual_landscaping = ops.landscaping_monthly * 12
    annual_cleaning = ops.cleaning_turnover_monthly * 12
    annual_accounting = ops.accounting_monthly * 12
    annual_licensing = ops.str_licensing_annual

    # Age-based reserves — use ops rates if caller overrode them, otherwise derive from age
    maint_pct, capex_pct = _age_based_reserve_rates(p.property_age_years)
    # Allow explicit overrides from OperatingExpenseInputs defaults
    if ops.maintenance_reserve_pct != 0.015 or ops.capex_reserve_pct != 0.010:
        maint_pct = ops.maintenance_reserve_pct
        capex_pct = ops.capex_reserve_pct
    annual_maintenance = p.purchase_price * maint_pct
    annual_capex = p.purchase_price * capex_pct

    total = (
        annual_mortgage + annual_property_tax + annual_insurance + annual_hoa +
        annual_utilities + annual_landscaping + annual_cleaning +
        annual_accounting + annual_licensing + annual_maintenance + annual_capex
    )

    return {
        "mortgage_monthly": monthly_pi,
        "mortgage_annual": annual_mortgage,
        "property_tax": annual_property_tax,
        "insurance_total": annual_insurance,
        "hoa": annual_hoa,
        "utilities": annual_utilities,
        "landscaping": annual_landscaping,
        "cleaning_turnover": annual_cleaning,
        "accounting": annual_accounting,
        "str_licensing": annual_licensing,
        "maintenance_reserve": annual_maintenance,
        "capex_reserve": annual_capex,
        "maintenance_reserve_pct": maint_pct,
        "capex_reserve_pct": capex_pct,
        "total_annual": total,
        "total_monthly": total / 12,
    }


def operating_expenses_ex_debt(exp: dict) -> float:
    """Total expenses excluding mortgage — used for NOI calculation."""
    return exp["total_annual"] - exp["mortgage_annual"]
