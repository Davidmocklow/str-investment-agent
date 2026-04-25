from .models import MarketInputs

# Calendar breakdown (days per year)
PEAK_DAYS = 92       # Jun, Jul, Aug
SHOULDER_DAYS = 122  # Apr, May, Sep, Oct
OFFSEASON_DAYS = 151 # Nov, Dec, Jan, Feb, Mar


def _allocate_personal_use(personal_days: int) -> tuple[int, int, int]:
    """
    Distributes personal-use days away from peak season first (per owner preference).
    Returns (peak_personal, shoulder_personal, offseason_personal).
    """
    offseason_personal = min(personal_days, OFFSEASON_DAYS)
    remaining = personal_days - offseason_personal
    shoulder_personal = min(remaining, SHOULDER_DAYS)
    remaining -= shoulder_personal
    peak_personal = min(remaining, PEAK_DAYS)
    return peak_personal, shoulder_personal, offseason_personal


def gross_rental_revenue(market: MarketInputs, personal_use_weeks: int = 4) -> dict:
    personal_days = personal_use_weeks * 7
    peak_personal, shoulder_personal, offseason_personal = _allocate_personal_use(personal_days)

    peak_avail = PEAK_DAYS - peak_personal
    shoulder_avail = SHOULDER_DAYS - shoulder_personal
    offseason_avail = OFFSEASON_DAYS - offseason_personal

    peak_rev = peak_avail * market.peak_occupancy * market.peak_adr
    shoulder_rev = shoulder_avail * market.shoulder_occupancy * market.shoulder_adr
    offseason_rev = offseason_avail * market.offseason_occupancy * market.offseason_adr
    gross = peak_rev + shoulder_rev + offseason_rev

    return {
        "peak_days_available": peak_avail,
        "shoulder_days_available": shoulder_avail,
        "offseason_days_available": offseason_avail,
        "peak_revenue": peak_rev,
        "shoulder_revenue": shoulder_rev,
        "offseason_revenue": offseason_rev,
        "gross_revenue": gross,
    }


def effective_gross_income(market: MarketInputs, personal_use_weeks: int = 4) -> dict:
    rev = gross_rental_revenue(market, personal_use_weeks)
    gross = rev["gross_revenue"]

    pm_fee = gross * market.pm_commission_rate
    platform_fee = gross * market.platform_fee_rate
    # Occupancy tax is collected from guests and remitted — not an income reduction,
    # but tracked here for gross-up visibility.
    occupancy_tax_collected = gross * market.occupancy_tax_rate

    egi = gross - pm_fee - platform_fee

    return {
        **rev,
        "pm_commission": pm_fee,
        "platform_fees": platform_fee,
        "occupancy_tax_collected": occupancy_tax_collected,
        "effective_gross_income": egi,
    }
