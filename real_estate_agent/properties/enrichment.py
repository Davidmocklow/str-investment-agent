"""
Bridges PropertyListing → financial model and attaches estimated cash-flow metrics.
Also resolves the MarketSnapshot for each listing by market_id.
"""

from __future__ import annotations

from real_estate_agent.scoring.models import MarketSnapshot, MarketCategory
from real_estate_agent.financial.models import (
    PropertyInputs, MarketInputs, FinancingInputs, InsuranceInputs,
    OperatingExpenseInputs, ScenarioInputs, FinancingType, MarketType,
)
from real_estate_agent.financial.metrics import calculate_all_metrics

from .models import PropertyListing

# Seasonal ADR multipliers relative to the market's annual median ADR
# Calibrated to coastal NC/SC seasonal patterns
_PEAK_MULT = 1.20
_SHOULDER_MULT = 0.78
_OFFSEASON_MULT = 0.50

_STATE_PROP_TAX = {"NC": 0.0070, "SC": 0.0055}
_STATE_MARKET_TYPE = {
    "NC": MarketType.COASTAL_NC,
    "SC": MarketType.COASTAL_SC,
}
_COASTAL_TIERS = {1, 2, 3}   # beach access tiers that warrant coastal windstorm insurance

# Flood insurance monthly cost by FEMA flood zone
_FLOOD_INSURANCE = {
    "X":  80.0,   # preferred zone — minimal flood risk
    "AE": 250.0,  # moderate risk — NFIP or private policy required
    "VE": 600.0,  # high coastal velocity zone — most expensive
}


def _property_adr_multiplier(listing: PropertyListing) -> float:
    """
    Adjusts the market's median 3bd ADR for property-specific characteristics.
    Returns a multiplier to apply before seasonal splits.
    Beach distance, pool, and bedroom count all affect achievable ADR.
    """
    mult = 1.0

    # Beach distance adjustment (market ADR is for a typical property ~1-3 mi out)
    d = listing.beach_distance_miles
    if d is not None:
        if d <= 0.1:
            mult *= 1.35   # oceanfront / beachfront premium
        elif d <= 0.5:
            mult *= 1.15   # close walk to beach
        elif d <= 1.0:
            mult *= 1.05   # short walk
        elif d <= 3.0:
            mult *= 1.00   # typical market property — no adj
        elif d <= 5.0:
            mult *= 0.90   # driving distance starts to hurt
        else:
            mult *= 0.78   # 5+ miles — material discount

    # Pool premium (additive on top of location)
    if listing.has_pool:
        mult *= 1.12

    # Bedroom count premium relative to 3bd market baseline
    if listing.bedrooms == 4:
        mult *= 1.28
    elif listing.bedrooms >= 5:
        mult *= 1.45

    return mult


def _market_inputs(snapshot: MarketSnapshot, listing: PropertyListing) -> MarketInputs:
    base_adr = snapshot.median_adr_3bd * _property_adr_multiplier(listing)
    return MarketInputs(
        peak_adr=base_adr * _PEAK_MULT,
        shoulder_adr=base_adr * _SHOULDER_MULT,
        offseason_adr=base_adr * _OFFSEASON_MULT,
        peak_occupancy=snapshot.peak_occupancy_rate,
        shoulder_occupancy=snapshot.shoulder_occupancy_rate,
        offseason_occupancy=snapshot.offseason_occupancy_rate,
        pm_commission_rate=0.25,
        platform_fee_rate=0.035,
        occupancy_tax_rate=0.085,
        property_tax_rate=_STATE_PROP_TAX.get(snapshot.state, 0.007),
        annual_appreciation_rate=snapshot.home_price_yoy_appreciation,  # no artificial floor
        annual_adr_growth_rate=0.03,
    )


def _insurance(snapshot: MarketSnapshot, listing: PropertyListing) -> InsuranceInputs:
    coastal = snapshot.beach_access_tier in _COASTAL_TIERS
    flood_zone = listing.flood_zone if listing.flood_zone else "X"
    return InsuranceInputs(
        homeowners_monthly=300.0,
        str_liability_monthly=175.0,
        windstorm_monthly=175.0 if coastal else 0.0,
        flood_monthly=_FLOOD_INSURANCE.get(flood_zone, 80.0),
    )


def _property_inputs(listing: PropertyListing, snapshot: MarketSnapshot) -> PropertyInputs:
    mtype = _STATE_MARKET_TYPE.get(snapshot.state, MarketType.COASTAL_NC)
    return PropertyInputs(
        purchase_price=listing.price,
        market_type=mtype,
        bedrooms=listing.bedrooms,
        has_pool=listing.has_pool,
        has_hoa=listing.has_hoa,
        hoa_monthly=listing.hoa_monthly,
        property_age_years=listing.effective_age,  # uses renovation_year if available
    )


def enrich(listing: PropertyListing, snapshot: MarketSnapshot, personal_use_weeks: int = 4) -> None:
    """Runs two financial scenarios (cash + DSCR) and attaches estimates to listing in-place."""
    listing.market_snapshot = snapshot

    market_in = _market_inputs(snapshot, listing)
    prop_in = _property_inputs(listing, snapshot)
    ins = _insurance(snapshot, listing)
    ops = OperatingExpenseInputs()  # reserves computed age-based in expenses.py

    # Cash scenario
    cash_scenario = ScenarioInputs(
        property=prop_in,
        market=market_in,
        financing=FinancingInputs(
            financing_type=FinancingType.CASH,
            down_payment=listing.price,
            interest_rate=0.0,
            loan_term_years=0,
        ),
        insurance=ins,
        operating=ops,
        annual_personal_use_weeks=personal_use_weeks,
        hold_period_years=5,
    )
    cash_metrics = calculate_all_metrics(cash_scenario)

    # DSCR scenario (30% down)
    dscr_down = listing.price * 0.30
    dscr_scenario = ScenarioInputs(
        property=prop_in,
        market=market_in,
        financing=FinancingInputs(
            financing_type=FinancingType.DSCR,
            down_payment=dscr_down,
            interest_rate=0.0775,
            loan_term_years=30,
        ),
        insurance=ins,
        operating=ops,
        annual_personal_use_weeks=personal_use_weeks,
        hold_period_years=5,
    )
    dscr_metrics = calculate_all_metrics(dscr_scenario)

    listing.estimated_egi_annual = cash_metrics["revenue"]["effective_gross_income"]
    listing.estimated_monthly_cf_cash = cash_metrics["monthly_cash_flow"]
    listing.estimated_monthly_cf_dscr = dscr_metrics["monthly_cash_flow"]
    listing.estimated_irr_cash_5yr = cash_metrics["irr"]
