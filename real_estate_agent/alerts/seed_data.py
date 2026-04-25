"""
Seeded demo data: realistic news articles and market snapshots for the alert demo.
All articles and prior-week snapshots are fictional but calibrated to real market conditions.
"""

from __future__ import annotations

import copy
from .models import NewsArticle
from real_estate_agent.scoring.models import MarketSnapshot
from real_estate_agent.scoring.markets import MARKETS_BY_ID


# ── Seeded news articles (simulating a week's News API + legislature RSS harvest) ──

SEED_ARTICLES: list[NewsArticle] = [

    NewsArticle(
        article_id="art_001",
        headline="Buncombe County Commission votes to extend owner-occupancy STR rule to unincorporated areas",
        body_snippet=(
            "The Buncombe County Commission voted 4-3 Tuesday to extend Asheville's owner-occupancy "
            "short-term rental requirement to unincorporated county areas, effective September 1, 2025. "
            "Non-owner-occupied vacation rental permits will no longer be issued outside city limits. "
            "Existing permit holders have 90 days to comply or cease operations."
        ),
        source_name="Asheville Citizen-Times",
        published_date="2025-04-23",
        url="https://example.com/buncombe-str-ordinance",
        market_hint="nc_asheville_buncombe",
    ),

    NewsArticle(
        article_id="art_002",
        headline="SC House Bill 4250 introduced: allows municipalities to require owner-occupancy for vacation rentals",
        body_snippet=(
            "South Carolina House Bill 4250, introduced this week, would amend the 2020 STR preemption law "
            "to allow municipalities to require owner-occupancy for short-term rentals in residential zones. "
            "If passed, it could affect all SC coastal markets including Hilton Head, Isle of Palms, and Pawleys Island. "
            "The bill is currently in the House Judiciary Committee with a hearing scheduled for May 14."
        ),
        source_name="The State (Columbia, SC)",
        published_date="2025-04-21",
        url="https://example.com/sc-hb4250",
        market_hint=None,  # state-wide — scanner will not map to specific market
    ),

    NewsArticle(
        article_id="art_003",
        headline="North Carolina Senate Bill 608 'STR Freedom Act' would preempt local short-term rental bans statewide",
        body_snippet=(
            "NC Senate Bill 608, introduced by Sen. Johnson (R-Wake), would prohibit municipalities from banning "
            "short-term rentals that hold a valid state STR license. The bill passed the Senate Commerce Committee "
            "on a 7-2 vote and heads to the full Senate floor. If enacted, it would effectively override Asheville's "
            "owner-occupancy requirement and prevent similar bans in other NC cities."
        ),
        source_name="NC Policy Watch",
        published_date="2025-04-22",
        url="https://example.com/nc-sb608",
        market_hint="nc_asheville_buncombe",
    ),

    NewsArticle(
        article_id="art_004",
        headline="Isle of Palms STR permit cap reached — no new short-term rental licenses until October review",
        body_snippet=(
            "The City of Isle of Palms announced this week that its annual cap of 1,400 active STR permits has been "
            "reached. No new permits will be issued until the October 2025 annual review. Existing permits are "
            "automatically renewed. Buyers should verify permit transferability before closing on any IOP property "
            "intended for short-term rental use."
        ),
        source_name="Post and Courier (Charleston)",
        published_date="2025-04-20",
        url="https://example.com/iop-permit-cap",
        market_hint="sc_isle_of_palms_charleston",
    ),

    NewsArticle(
        article_id="art_005",
        headline="Hurricane season 2025: NOAA predicts above-normal season, NC Outer Banks and SC coast at elevated risk",
        body_snippet=(
            "NOAA's 2025 Atlantic hurricane season outlook predicts 17–25 named storms with 8–13 hurricanes. "
            "The NC Outer Banks, Crystal Coast, Hilton Head, and Myrtle Beach areas face above-normal landfall probability. "
            "STR investors on the coast should verify wind and flood insurance coverage is adequate. "
            "Peak hurricane risk period: August 15 – October 15."
        ),
        source_name="NOAA / Weather.gov",
        published_date="2025-04-18",
        url="https://example.com/noaa-2025-forecast",
        market_hint="nc_obx_dare",
    ),

    NewsArticle(
        article_id="art_006",
        headline="Dare County launches new STR registry — $75 annual fee, no permit caps or new restrictions",
        body_snippet=(
            "Dare County announced a new short-term rental registry effective July 1, 2025, requiring all STR "
            "operators to register annually at a fee of $75/year. The registry is informational only — no caps "
            "on new registrations and no owner-occupancy requirements. Officials emphasized the registry is "
            "for emergency contact purposes, not regulation."
        ),
        source_name="Outer Banks Voice",
        published_date="2025-04-19",
        url="https://example.com/dare-registry",
        market_hint="nc_obx_dare",
    ),

    NewsArticle(
        article_id="art_007",
        headline="Myrtle Beach STR market showing signs of oversupply as new condo-hotel inventory enters market",
        body_snippet=(
            "Horry County STR analysts note that active vacation rental listings in the Grand Strand grew 14% "
            "in Q1 2025, driven largely by new condo-hotel inventory in North Myrtle Beach. Occupancy rates "
            "are holding but average daily rates have softened 7% compared to Q1 2024. Property managers "
            "report increased competition for bookings in the $150–250/night range."
        ),
        source_name="Myrtle Beach Sun News",
        published_date="2025-04-17",
        url="https://example.com/mb-oversupply",
        market_hint="sc_myrtle_beach_horry",
    ),

    NewsArticle(
        article_id="art_008",
        headline="Lake Lure recovery update: 90% of STR properties operational as Helene infrastructure repairs complete",
        body_snippet=(
            "Rutherford County tourism officials report that 90% of short-term rental properties impacted by "
            "Hurricane Helene in September 2024 are now operational. Highway 74 and Lake Lure Dam access roads "
            "have been fully restored. Bookings are tracking 15% below pre-Helene levels but officials expect "
            "full recovery by summer 2025 peak season."
        ),
        source_name="Rutherford County News",
        published_date="2025-04-16",
        url="https://example.com/lake-lure-recovery",
        market_hint="nc_lake_lure_rutherford",
    ),
]


# ── Prior-week market snapshots (simulating stored weekly history) ─────────────
# Used by market condition triggers to detect delta-based changes.

def build_prior_snapshots() -> dict[str, MarketSnapshot]:
    """
    Returns slightly modified prior-week snapshots for demo purposes.
    In production, these are loaded from the weekly snapshot database.
    """
    priors: dict[str, MarketSnapshot] = {}

    for market_id, snap in MARKETS_BY_ID.items():
        prior = copy.deepcopy(snap)

        # Simulate Myrtle Beach: ADR dropped 8% week-over-week (oversupply kicking in)
        if market_id == "sc_myrtle_beach_horry":
            prior.median_adr_3bd = snap.median_adr_3bd / 0.92   # prior was higher
            prior.listings_yoy_growth = 0.09                     # supply surge accelerating

        # Simulate Lake Lure: recovery — occupancy was lower last week
        if market_id == "nc_lake_lure_rutherford":
            prior.annual_occupancy_rate = snap.annual_occupancy_rate - 0.04

        # Simulate OBX: modest ADR appreciation (positive signal)
        if market_id == "nc_obx_dare":
            prior.median_adr_3bd = snap.median_adr_3bd * 0.89   # ADR surged this week

        # Simulate Crystal Coast: supply accelerating (warning signal)
        if market_id == "nc_crystal_coast_carteret":
            prior.listings_yoy_growth = 0.04    # was 4%, now 8% — threshold crossed

        priors[market_id] = prior

    return priors
