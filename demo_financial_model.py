"""
Demo: Three financing scenarios for a representative NC coastal property.

Property:  3bd/3ba, built ~2015, no HOA, within 10mi of beach (no pool)
Market:    Crystal Coast / Outer Banks, NC
Price:     $750,000
Down:      $225,000 (30%)

Scenarios:
  1. DSCR loan  @ 7.75%  (trust-friendly, standard for STR investors)
  2. Portfolio  @ 8.25%  (trust-friendly, held by bank)
  3. All-cash   purchase  (eliminates debt service entirely)
"""

from real_estate_agent.financial.models import (
    PropertyInputs,
    MarketInputs,
    FinancingInputs,
    InsuranceInputs,
    OperatingExpenseInputs,
    ScenarioInputs,
    FinancingType,
    MarketType,
)
from real_estate_agent.financial.proforma import generate_proforma, print_proforma, compare_scenarios


# ── Property ──────────────────────────────────────────────────────────────────
PROPERTY = PropertyInputs(
    purchase_price=750_000,
    market_type=MarketType.COASTAL_NC,
    bedrooms=3,
    has_pool=False,
    has_hoa=False,
    hoa_monthly=0.0,
    property_age_years=10,
)

# ── Market (Crystal Coast / Southern OBX, NC) ─────────────────────────────────
# Source: AirDNA regional averages Q1 2025 for 3bd coastal NC STR
MARKET = MarketInputs(
    peak_adr=425.0,          # Jun–Aug nightly avg ($375–$500 range for 3bd)
    shoulder_adr=280.0,      # Apr–May, Sep–Oct
    offseason_adr=185.0,     # Nov–Mar
    peak_occupancy=0.87,     # Regional AirDNA avg
    shoulder_occupancy=0.68,
    offseason_occupancy=0.42,
    pm_commission_rate=0.25,  # 25% — standard Crystal Coast / OBX PM rate
    platform_fee_rate=0.035,  # Blended Airbnb + VRBO
    occupancy_tax_rate=0.085, # Carteret / Dare County combined rate
    property_tax_rate=0.007,  # ~0.7% coastal NC
    annual_appreciation_rate=0.04,
    annual_adr_growth_rate=0.03,
)

# ── Insurance (coastal NC — AE flood zone, windstorm required) ───────────────────
INSURANCE = InsuranceInputs(
    homeowners_monthly=300.0,
    str_liability_monthly=175.0,
    windstorm_monthly=175.0,    # hurricane/wind rider for coastal NC
    flood_monthly=250.0,        # AE flood zone NFIP / private policy
)

# ── Operating expenses ────────────────────────────────────────────────────────
OPERATING = OperatingExpenseInputs(
    utilities_monthly=450.0,
    landscaping_monthly=200.0,
    cleaning_turnover_monthly=200.0,
    maintenance_reserve_pct=0.015,
    capex_reserve_pct=0.010,
    str_licensing_annual=500.0,
    accounting_monthly=150.0,
)

# ── Three financing scenarios ──────────────────────────────────────────────────
scenarios = [
    ScenarioInputs(
        property=PROPERTY,
        market=MARKET,
        financing=FinancingInputs(
            financing_type=FinancingType.DSCR,
            down_payment=225_000,
            interest_rate=0.0775,
            loan_term_years=30,
        ),
        insurance=INSURANCE,
        operating=OPERATING,
        annual_personal_use_weeks=4,
        hold_period_years=5,
    ),
    ScenarioInputs(
        property=PROPERTY,
        market=MARKET,
        financing=FinancingInputs(
            financing_type=FinancingType.PORTFOLIO,
            down_payment=225_000,
            interest_rate=0.0825,
            loan_term_years=30,
        ),
        insurance=INSURANCE,
        operating=OPERATING,
        annual_personal_use_weeks=4,
        hold_period_years=5,
    ),
    ScenarioInputs(
        property=PROPERTY,
        market=MARKET,
        financing=FinancingInputs(
            financing_type=FinancingType.CASH,
            down_payment=750_000,
            interest_rate=0.0,
            loan_term_years=0,
        ),
        insurance=INSURANCE,
        operating=OPERATING,
        annual_personal_use_weeks=4,
        hold_period_years=5,
    ),
]

NAMES = [
    "DSCR @ 7.75%  —  $225k down (30%)",
    "Portfolio @ 8.25%  —  $225k down (30%)",
    "All-Cash Purchase  —  $750k",
]


if __name__ == "__main__":
    results = []
    for scenario, name in zip(scenarios, NAMES):
        r = generate_proforma(scenario, name)
        results.append(r)
        print_proforma(r)

    compare_scenarios(results)

    print("NOTE: All figures use stated regional market averages.")
    print("      Actual results depend on property location, amenities, and management quality.")
    print("      DSCR/Portfolio rates reflect early-2026 market; verify with lenders.")
    print("      Irrevocable trust financing: confirm lender trust-vesting policy before proceeding.\n")
