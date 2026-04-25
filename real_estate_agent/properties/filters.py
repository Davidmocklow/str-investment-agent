"""
Hard filters — any failure excludes the property entirely from the scored list.
These are non-negotiable criteria based on owner requirements.
"""

from .models import PropertyListing, FilterResult
from real_estate_agent.scoring.models import MarketSnapshot, RegulatoryStatus

# Thresholds matching owner spec
MIN_PRICE = 600_000
MAX_PRICE = 1_200_000
MIN_BEDS = 3
MIN_BATHS = 3.0
MAX_AGE_YEARS = 25             # built 2000 or later; older OK if substantially renovated
MAX_RENOVATION_AGE = 5         # major renovation within last 5 years clears the age filter
MAX_HOA_MONTHLY = 300          # tolerable only if STR-permitted
MAX_AIRPORT_MIN = 90           # relaxed from 60 — OBX/ORF is ~75-80 min
MAX_BEACH_MILES = 10           # pool is acceptable alternative
MAX_HOA_MONTHLY_UNKNOWN = 150  # if STR permission unknown, be conservative


def apply_filters(listing: PropertyListing, market: MarketSnapshot) -> FilterResult:
    reasons: list[str] = []

    if listing.price < MIN_PRICE:
        reasons.append(f"Price ${listing.price:,.0f} below minimum ${MIN_PRICE:,.0f}")
    if listing.price > MAX_PRICE:
        reasons.append(f"Price ${listing.price:,.0f} exceeds maximum ${MAX_PRICE:,.0f}")

    if listing.bedrooms < MIN_BEDS:
        reasons.append(f"Only {listing.bedrooms} bedrooms (min {MIN_BEDS})")
    if listing.bathrooms < MIN_BATHS:
        reasons.append(f"Only {listing.bathrooms} baths (min {MIN_BATHS})")

    if listing.age > MAX_AGE_YEARS:
        # Pass if a major renovation was done within the last MAX_RENOVATION_AGE years
        renovation_ok = (
            listing.renovation_year is not None and
            (2025 - listing.renovation_year) <= MAX_RENOVATION_AGE
        )
        if not renovation_ok:
            reasons.append(
                f"Built {listing.year_built} — {listing.age} years old (max {MAX_AGE_YEARS}"
                + (f", renovated {listing.renovation_year}" if listing.renovation_year else "") + ")"
            )

    # HOA logic
    if listing.has_hoa:
        if listing.hoa_str_permitted is False:
            reasons.append("HOA explicitly prohibits short-term rentals")
        elif listing.hoa_str_permitted is None and listing.hoa_monthly > MAX_HOA_MONTHLY_UNKNOWN:
            reasons.append(f"HOA ${listing.hoa_monthly:.0f}/mo with unknown STR permission — too risky")
        elif listing.hoa_monthly > MAX_HOA_MONTHLY:
            reasons.append(f"HOA ${listing.hoa_monthly:.0f}/mo exceeds ${MAX_HOA_MONTHLY}/mo cap")

    # Beach or pool requirement
    beach_ok = listing.beach_distance_miles is not None and listing.beach_distance_miles <= MAX_BEACH_MILES
    pool_ok = listing.has_pool
    if not beach_ok and not pool_ok:
        miles = f"{listing.beach_distance_miles:.1f}mi" if listing.beach_distance_miles else "unknown"
        reasons.append(f"No pool and beach is {miles} away (max {MAX_BEACH_MILES}mi)")

    # Airport — flag as warning rather than hard exclude (market-level filter already applied)
    if listing.airport_drive_min > MAX_AIRPORT_MIN:
        reasons.append(f"Airport {listing.airport_code} is {listing.airport_drive_min} min drive (preference ≤{MAX_AIRPORT_MIN})")

    # Market-level regulatory exclusion
    if market.regulatory_status == RegulatoryStatus.RESTRICTIVE:
        reasons.append(f"Market '{market.name}' is RESTRICTIVE for STR — high ban risk")

    return FilterResult(passed=len(reasons) == 0, failed_reasons=reasons)
