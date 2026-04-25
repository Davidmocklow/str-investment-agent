"""
Seeded sample listings — 22 realistic properties across the top 8 tracked markets.
Includes intentional hard-filter failures for demonstration.

Prices, sizes, and characteristics calibrated to actual Q1 2025 market conditions.
Replace with live Zillow / Realtor.com API calls once subscriptions are active.
"""

from __future__ import annotations

from real_estate_agent.properties.models import PropertyListing
from .base import ListingSource


_LISTINGS: list[PropertyListing] = [

    # ── CRYSTAL COAST / CARTERET COUNTY, NC  (#4 market) ──────────────────────

    PropertyListing(
        listing_id="seed_cc_01",
        source="seed", url="https://example.com/seed_cc_01",
        address="214 Ocean Drive", city="Emerald Isle", state="NC", zip_code="28594",
        market_id="nc_crystal_coast_carteret",
        price=699_000, bedrooms=3, bathrooms=3.0, sqft=1_820, year_built=2018,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.1, airport_code="EWN", airport_drive_min=35,
        flood_zone="AE",
        days_on_market=42, original_list_price=725_000, price_reduction=26_000,
    ),
    PropertyListing(
        listing_id="seed_cc_02",
        source="seed", url="https://example.com/seed_cc_02",
        address="87 Bogue Sound Ln", city="Atlantic Beach", state="NC", zip_code="28512",
        market_id="nc_crystal_coast_carteret",
        price=624_000, bedrooms=3, bathrooms=3.0, sqft=1_650, year_built=2014,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=False,
        beach_distance_miles=1.8, airport_code="EWN", airport_drive_min=37,
        flood_zone="X",
        days_on_market=19, original_list_price=624_000, price_reduction=0,
    ),
    PropertyListing(
        listing_id="seed_cc_03",
        source="seed", url="https://example.com/seed_cc_03",
        address="512 Salter Path Rd", city="Pine Knoll Shores", state="NC", zip_code="28512",
        market_id="nc_crystal_coast_carteret",
        price=875_000, bedrooms=4, bathrooms=3.5, sqft=2_340, year_built=2019,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.4, airport_code="EWN", airport_drive_min=33,
        flood_zone="AE",
        days_on_market=67, original_list_price=950_000, price_reduction=75_000,
    ),

    # ── OUTER BANKS / DARE COUNTY, NC  (#5 market) ────────────────────────────

    PropertyListing(
        listing_id="seed_obx_01",
        source="seed", url="https://example.com/seed_obx_01",
        address="1102 S Virginia Dare Tr", city="Kill Devil Hills", state="NC", zip_code="27948",
        market_id="nc_obx_dare",
        price=719_000, bedrooms=3, bathrooms=3.0, sqft=1_780, year_built=2016,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=False,
        beach_distance_miles=0.3, airport_code="ORF", airport_drive_min=75,
        flood_zone="X",
        days_on_market=31, original_list_price=740_000, price_reduction=21_000,
    ),
    PropertyListing(
        listing_id="seed_obx_02",
        source="seed", url="https://example.com/seed_obx_02",
        address="403 E Admiral St", city="Nags Head", state="NC", zip_code="27959",
        market_id="nc_obx_dare",
        price=849_000, bedrooms=4, bathrooms=3.0, sqft=2_150, year_built=2015,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.1, airport_code="ORF", airport_drive_min=80,
        flood_zone="AE",
        days_on_market=54, original_list_price=899_000, price_reduction=50_000,
    ),
    PropertyListing(
        listing_id="seed_obx_03",    # FAILS: airport > 60 min (Corolla)
        source="seed", url="https://example.com/seed_obx_03",
        address="812 Ocean Trail", city="Corolla", state="NC", zip_code="27927",
        market_id="nc_obx_dare",
        price=995_000, bedrooms=3, bathrooms=4.0, sqft=2_600, year_built=2020,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.8, airport_code="ORF", airport_drive_min=92,
        flood_zone="X",
        days_on_market=28, original_list_price=995_000, price_reduction=0,
    ),

    # ── HILTON HEAD ISLAND, SC  (#1 market) ───────────────────────────────────

    PropertyListing(
        listing_id="seed_hhh_01",
        source="seed", url="https://example.com/seed_hhh_01",
        address="22 Turtle Cove Ln", city="Hilton Head Island", state="SC", zip_code="29928",
        market_id="sc_hilton_head_beaufort",
        price=789_000, bedrooms=3, bathrooms=3.0, sqft=1_940, year_built=2017,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.6, airport_code="HHH", airport_drive_min=12,
        flood_zone="X",
        days_on_market=38, original_list_price=825_000, price_reduction=36_000,
    ),
    PropertyListing(
        listing_id="seed_hhh_02",   # FAILS: HOA bans STR (Forest Beach/Hilton Head Plantation)
        source="seed", url="https://example.com/seed_hhh_02",
        address="45 Plantation Club Dr", city="Hilton Head Island", state="SC", zip_code="29926",
        market_id="sc_hilton_head_beaufort",
        price=940_000, bedrooms=3, bathrooms=3.5, sqft=2_280, year_built=2016,
        property_type="single_family",
        has_hoa=True, hoa_monthly=285, hoa_str_permitted=False,
        has_pool=False,
        beach_distance_miles=3.2, airport_code="HHH", airport_drive_min=18,
        flood_zone="X",
        days_on_market=62, original_list_price=985_000, price_reduction=45_000,
    ),
    PropertyListing(
        listing_id="seed_hhh_03",
        source="seed", url="https://example.com/seed_hhh_03",
        address="7 Folly Field Rd", city="Hilton Head Island", state="SC", zip_code="29928",
        market_id="sc_hilton_head_beaufort",
        price=1_050_000, bedrooms=4, bathrooms=4.0, sqft=2_680, year_built=2021,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.2, airport_code="HHH", airport_drive_min=10,
        flood_zone="AE",
        days_on_market=22, original_list_price=1_075_000, price_reduction=25_000,
    ),

    # ── PAWLEYS ISLAND / LITCHFIELD BEACH, SC  (#2 market) ────────────────────

    PropertyListing(
        listing_id="seed_pi_01",
        source="seed", url="https://example.com/seed_pi_01",
        address="314 Litchfield Beach Dr", city="Pawleys Island", state="SC", zip_code="29585",
        market_id="sc_pawleys_georgetown",
        price=589_000, bedrooms=3, bathrooms=3.0, sqft=1_760, year_built=2015,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=False,
        beach_distance_miles=2.1, airport_code="MYR", airport_drive_min=28,
        flood_zone="X",
        days_on_market=55, original_list_price=625_000, price_reduction=36_000,
    ),
    PropertyListing(
        listing_id="seed_pi_02",
        source="seed", url="https://example.com/seed_pi_02",
        address="81 Creek Bend Ct", city="Litchfield Beach", state="SC", zip_code="29585",
        market_id="sc_pawleys_georgetown",
        price=725_000, bedrooms=4, bathrooms=3.0, sqft=2_100, year_built=2018,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=1.4, airport_code="MYR", airport_drive_min=30,
        flood_zone="X",
        days_on_market=14, original_list_price=725_000, price_reduction=0,
    ),
    PropertyListing(
        listing_id="seed_pi_03",   # FAILS: built 2003 (>20 yr old)
        source="seed", url="https://example.com/seed_pi_03",
        address="25 Sea Island Dr", city="Pawleys Island", state="SC", zip_code="29585",
        market_id="sc_pawleys_georgetown",
        price=638_000, bedrooms=3, bathrooms=3.0, sqft=1_820, year_built=2003,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=False,
        beach_distance_miles=4.5, airport_code="MYR", airport_drive_min=26,
        flood_zone="X",
        days_on_market=88, original_list_price=699_000, price_reduction=61_000,
    ),

    # ── ISLE OF PALMS, SC  (#3 market) ────────────────────────────────────────

    PropertyListing(
        listing_id="seed_iop_01",
        source="seed", url="https://example.com/seed_iop_01",
        address="18 Ocean Blvd", city="Isle of Palms", state="SC", zip_code="29451",
        market_id="sc_isle_of_palms_charleston",
        price=1_095_000, bedrooms=3, bathrooms=3.0, sqft=2_050, year_built=2019,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=False,
        beach_distance_miles=0.1, airport_code="CHS", airport_drive_min=32,
        flood_zone="AE",
        days_on_market=44, original_list_price=1_150_000, price_reduction=55_000,
    ),
    PropertyListing(
        listing_id="seed_iop_02",
        source="seed", url="https://example.com/seed_iop_02",
        address="502 Palm Blvd", city="Isle of Palms", state="SC", zip_code="29451",
        market_id="sc_isle_of_palms_charleston",
        price=1_175_000, bedrooms=4, bathrooms=3.5, sqft=2_420, year_built=2020,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.3, airport_code="CHS", airport_drive_min=32,
        flood_zone="AE",
        days_on_market=18, original_list_price=1_195_000, price_reduction=20_000,
    ),

    # ── TOPSAIL ISLAND / PENDER COUNTY, NC  (#6 market) ──────────────────────

    PropertyListing(
        listing_id="seed_ti_01",
        source="seed", url="https://example.com/seed_ti_01",
        address="636 N Anderson Blvd", city="Surf City", state="NC", zip_code="28445",
        market_id="nc_topsail_pender",
        price=649_000, bedrooms=3, bathrooms=3.0, sqft=1_720, year_built=2017,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=False,
        beach_distance_miles=0.2, airport_code="ILM", airport_drive_min=45,
        flood_zone="AE",
        days_on_market=36, original_list_price=675_000, price_reduction=26_000,
    ),
    PropertyListing(
        listing_id="seed_ti_02",
        source="seed", url="https://example.com/seed_ti_02",
        address="115 Bridgette Blvd", city="North Topsail Beach", state="NC", zip_code="28460",
        market_id="nc_topsail_pender",
        price=745_000, bedrooms=3, bathrooms=3.5, sqft=2_010, year_built=2020,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.1, airport_code="ILM", airport_drive_min=50,
        flood_zone="AE",
        days_on_market=21, original_list_price=765_000, price_reduction=20_000,
    ),

    # ── WILMINGTON / WRIGHTSVILLE BEACH, NC  (#9 market) ──────────────────────

    PropertyListing(
        listing_id="seed_wil_01",
        source="seed", url="https://example.com/seed_wil_01",
        address="308 Wrightsville Ave", city="Wrightsville Beach", state="NC", zip_code="28480",
        market_id="nc_wilmington_nhc",
        price=985_000, bedrooms=3, bathrooms=3.0, sqft=1_980, year_built=2016,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=False,
        beach_distance_miles=0.1, airport_code="ILM", airport_drive_min=12,
        flood_zone="AE",
        days_on_market=72, original_list_price=1_050_000, price_reduction=65_000,
    ),

    # ── MYRTLE BEACH / HORRY COUNTY, SC  (#8 market) ─────────────────────────

    PropertyListing(
        listing_id="seed_mb_01",
        source="seed", url="https://example.com/seed_mb_01",
        address="4422 N Ocean Blvd", city="North Myrtle Beach", state="SC", zip_code="29582",
        market_id="sc_myrtle_beach_horry",
        price=618_000, bedrooms=3, bathrooms=3.0, sqft=1_680, year_built=2018,
        property_type="single_family",
        has_hoa=False, hoa_monthly=0, hoa_str_permitted=None,
        has_pool=True,
        beach_distance_miles=0.4, airport_code="MYR", airport_drive_min=10,
        flood_zone="X",
        days_on_market=48, original_list_price=660_000, price_reduction=42_000,
    ),

    # ── INTENTIONAL HARD-FILTER FAILURES (for demo transparency) ─────────────

    PropertyListing(
        listing_id="seed_fail_01",   # FAILS: price $1.32m > $1.2m max
        source="seed", url="https://example.com/seed_fail_01",
        address="99 Oceanfront Way", city="Kiawah Island", state="SC", zip_code="29455",
        market_id="sc_kiawah_charleston",
        price=1_320_000, bedrooms=4, bathrooms=4.0, sqft=3_100, year_built=2021,
        property_type="single_family",
        has_hoa=True, hoa_monthly=450, hoa_str_permitted=False,
        has_pool=True,
        beach_distance_miles=0.1, airport_code="CHS", airport_drive_min=45,
        flood_zone="AE",
        days_on_market=15, original_list_price=1_350_000, price_reduction=30_000,
    ),
    PropertyListing(
        listing_id="seed_fail_02",   # FAILS: market is RESTRICTIVE (Kiawah POA)
        source="seed", url="https://example.com/seed_fail_02",
        address="14 Egret Marsh Ct", city="Kiawah Island", state="SC", zip_code="29455",
        market_id="sc_kiawah_charleston",
        price=895_000, bedrooms=3, bathrooms=3.0, sqft=2_200, year_built=2019,
        property_type="single_family",
        has_hoa=True, hoa_monthly=380, hoa_str_permitted=False,
        has_pool=False,
        beach_distance_miles=1.2, airport_code="CHS", airport_drive_min=45,
        flood_zone="X",
        days_on_market=90, original_list_price=960_000, price_reduction=65_000,
    ),
]


class SeedSource(ListingSource):
    name = "seed"

    def fetch(self, market_ids: list[str] | None = None) -> list[PropertyListing]:
        if market_ids is None:
            return list(_LISTINGS)
        return [l for l in _LISTINGS if l.market_id in market_ids]
