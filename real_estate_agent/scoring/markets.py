"""
Seeded market snapshots for all tracked NC/SC markets.

Data calibrated from AirDNA public market reports, Zillow Research, and
published STR studies (Q1 2025). Replace with live API calls once
AirDNA and Zillow subscriptions are active.

Airport drive times are conservative estimates from mid-market ZIP codes.
Golf course counts sourced from NCGA / SCGA public directories.
"""

from .models import MarketSnapshot, MarketCategory, RegulatoryStatus

MARKETS: list[MarketSnapshot] = [

    # ── COASTAL NC ────────────────────────────────────────────────────────────

    MarketSnapshot(
        market_id="nc_obx_dare",
        name="Outer Banks (Dare County)",
        state="NC",
        category=MarketCategory.COASTAL_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        # STR metrics — OBX is one of the strongest coastal STR markets on the east coast
        annual_occupancy_rate=0.68,
        peak_occupancy_rate=0.91,
        shoulder_occupancy_rate=0.72,
        offseason_occupancy_rate=0.38,
        median_adr_3bd=415.0,
        adr_yoy_growth=0.04,
        annual_revpan=243.0,     # $415 * blended ~58.5% effective occupancy
        active_listings=5800,
        listings_yoy_growth=0.06,
        # Property market
        median_home_price=725_000,
        home_price_yoy_appreciation=0.05,
        # Geography — ORF (Norfolk) is ~75 min from Kill Devil Hills; borderline
        nearest_airport_code="ORF",
        nearest_airport_drive_min=75,
        beach_access_tier=1,
        golf_courses_30mi=4,
        # Regulatory — NC coastal generally stable; some Dare County permit requirements
        regulatory_status=RegulatoryStatus.STABLE,
        regulatory_notes="Dare County requires STR permit ($50/yr). No density caps or ban proposals as of Q1 2025.",
        hoa_str_risk=False,
    ),

    MarketSnapshot(
        market_id="nc_crystal_coast_carteret",
        name="Crystal Coast (Carteret County)",
        state="NC",
        category=MarketCategory.COASTAL_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.65,
        peak_occupancy_rate=0.87,
        shoulder_occupancy_rate=0.68,
        offseason_occupancy_rate=0.36,
        median_adr_3bd=350.0,
        adr_yoy_growth=0.05,
        annual_revpan=197.0,
        active_listings=3200,
        listings_yoy_growth=0.08,
        median_home_price=620_000,
        home_price_yoy_appreciation=0.06,
        # EWN (New Bern Regional) is ~35 min; small airport but has commercial service
        nearest_airport_code="EWN",
        nearest_airport_drive_min=35,
        beach_access_tier=1,
        golf_courses_30mi=7,
        regulatory_status=RegulatoryStatus.STABLE,
        regulatory_notes="Carteret County has light registration requirements. No STR restrictions in unincorporated areas.",
        hoa_str_risk=False,
    ),

    MarketSnapshot(
        market_id="nc_wilmington_nhc",
        name="Wilmington / Wrightsville Beach",
        state="NC",
        category=MarketCategory.COASTAL_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.66,
        peak_occupancy_rate=0.84,
        shoulder_occupancy_rate=0.70,
        offseason_occupancy_rate=0.42,
        median_adr_3bd=295.0,
        adr_yoy_growth=0.03,
        annual_revpan=178.0,
        active_listings=4100,
        listings_yoy_growth=0.11,
        median_home_price=585_000,
        home_price_yoy_appreciation=0.04,
        nearest_airport_code="ILM",
        nearest_airport_drive_min=12,
        beach_access_tier=2,
        golf_courses_30mi=14,
        # City of Wilmington enacted STR overlay districts; Wrightsville Beach has caps
        regulatory_status=RegulatoryStatus.EVOLVING_BENIGN,
        regulatory_notes="City of Wilmington requires annual STR license. Wrightsville Beach limits new permits. County areas permissive.",
        hoa_str_risk=False,
    ),

    MarketSnapshot(
        market_id="nc_topsail_pender",
        name="Topsail Island (Pender / Onslow)",
        state="NC",
        category=MarketCategory.COASTAL_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.62,
        peak_occupancy_rate=0.86,
        shoulder_occupancy_rate=0.64,
        offseason_occupancy_rate=0.30,
        median_adr_3bd=305.0,
        adr_yoy_growth=0.06,
        annual_revpan=167.0,
        active_listings=1800,
        listings_yoy_growth=0.10,
        median_home_price=545_000,
        home_price_yoy_appreciation=0.05,
        # ILM is ~45 min from Surf City; reasonable
        nearest_airport_code="ILM",
        nearest_airport_drive_min=45,
        beach_access_tier=1,
        golf_courses_30mi=9,
        regulatory_status=RegulatoryStatus.STABLE,
        regulatory_notes="Surf City and Holly Ridge have minimal STR regulation. Growing market with no active restriction proposals.",
        hoa_str_risk=False,
    ),

    # ── COASTAL SC ────────────────────────────────────────────────────────────

    MarketSnapshot(
        market_id="sc_hilton_head_beaufort",
        name="Hilton Head Island",
        state="SC",
        category=MarketCategory.COASTAL_SC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.71,
        peak_occupancy_rate=0.92,
        shoulder_occupancy_rate=0.74,
        offseason_occupancy_rate=0.44,
        median_adr_3bd=440.0,
        adr_yoy_growth=0.04,
        annual_revpan=272.0,
        active_listings=6200,
        listings_yoy_growth=0.05,
        median_home_price=820_000,
        home_price_yoy_appreciation=0.05,
        # HHH on-island (~10 min from most areas); SAV is backup at ~45 min
        nearest_airport_code="HHH",
        nearest_airport_drive_min=12,
        beach_access_tier=1,
        golf_courses_30mi=28,    # golf mecca — over 20 courses on/near island
        # Town of HHH has STR permit system; SC preempts local bans but allows registration
        regulatory_status=RegulatoryStatus.EVOLVING_BENIGN,
        regulatory_notes="Town permit required ($150/yr). SC HB 3525 allows local registration but prohibits outright bans. Stable since 2021.",
        hoa_str_risk=True,    # Many HHH properties are in POA communities with STR restrictions
    ),

    MarketSnapshot(
        market_id="sc_isle_of_palms_charleston",
        name="Isle of Palms / Sullivan's Island",
        state="SC",
        category=MarketCategory.COASTAL_SC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.68,
        peak_occupancy_rate=0.90,
        shoulder_occupancy_rate=0.70,
        offseason_occupancy_rate=0.40,
        median_adr_3bd=405.0,
        adr_yoy_growth=0.03,
        annual_revpan=242.0,
        active_listings=1400,
        listings_yoy_growth=0.04,
        median_home_price=1_050_000,
        home_price_yoy_appreciation=0.06,
        nearest_airport_code="CHS",
        nearest_airport_drive_min=32,
        beach_access_tier=1,
        golf_courses_30mi=18,
        # IOP allows STR with permit; Sullivan's Island has very strict limits (effectively banned)
        regulatory_status=RegulatoryStatus.EVOLVING_BENIGN,
        regulatory_notes="IOP requires rental permit and annual inspection. Sullivan's Island near-ban on STR. Stick to IOP properties.",
        hoa_str_risk=False,
    ),

    MarketSnapshot(
        market_id="sc_pawleys_georgetown",
        name="Pawleys Island / Litchfield Beach",
        state="SC",
        category=MarketCategory.COASTAL_SC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.63,
        peak_occupancy_rate=0.85,
        shoulder_occupancy_rate=0.65,
        offseason_occupancy_rate=0.34,
        median_adr_3bd=310.0,
        adr_yoy_growth=0.05,
        annual_revpan=173.0,
        active_listings=1100,
        listings_yoy_growth=0.07,
        median_home_price=560_000,
        home_price_yoy_appreciation=0.05,
        nearest_airport_code="MYR",
        nearest_airport_drive_min=28,
        beach_access_tier=1,
        golf_courses_30mi=22,    # Grand Strand golf proximity
        regulatory_status=RegulatoryStatus.STABLE,
        regulatory_notes="Georgetown County is STR-permissive. No active restriction proposals. Light registration only.",
        hoa_str_risk=False,
    ),

    MarketSnapshot(
        market_id="sc_myrtle_beach_horry",
        name="Myrtle Beach (Grand Strand)",
        state="SC",
        category=MarketCategory.COASTAL_SC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.64,
        peak_occupancy_rate=0.88,
        shoulder_occupancy_rate=0.67,
        offseason_occupancy_rate=0.35,
        median_adr_3bd=230.0,
        adr_yoy_growth=0.02,
        annual_revpan=130.0,
        active_listings=14_500,   # very high supply — saturated market
        listings_yoy_growth=0.09,
        median_home_price=410_000,
        home_price_yoy_appreciation=0.03,
        nearest_airport_code="MYR",
        nearest_airport_drive_min=10,
        beach_access_tier=1,
        golf_courses_30mi=35,    # 90+ golf courses in Grand Strand area
        regulatory_status=RegulatoryStatus.EVOLVING_BENIGN,
        regulatory_notes="Horry County STR-friendly. City of Myrtle Beach has permit system. No ban proposals. High supply is primary risk.",
        hoa_str_risk=False,
    ),

    MarketSnapshot(
        market_id="sc_kiawah_charleston",
        name="Kiawah / Seabrook Islands",
        state="SC",
        category=MarketCategory.COASTAL_SC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.70,
        peak_occupancy_rate=0.91,
        shoulder_occupancy_rate=0.72,
        offseason_occupancy_rate=0.44,
        median_adr_3bd=520.0,
        adr_yoy_growth=0.04,
        annual_revpan=306.0,
        active_listings=900,
        listings_yoy_growth=0.03,
        median_home_price=1_150_000,
        home_price_yoy_appreciation=0.07,
        nearest_airport_code="CHS",
        nearest_airport_drive_min=45,
        beach_access_tier=1,
        golf_courses_30mi=20,
        # WARNING: Kiawah POA and Seabrook POA control STR tightly. Many villa
        # zones allow STR through the official resort rental program only.
        # Private STR platforms effectively banned in most residential zones.
        regulatory_status=RegulatoryStatus.RESTRICTIVE,
        regulatory_notes="Kiawah/Seabrook POAs enforce STR through resort programs only. Airbnb/VRBO listings in most zones violate POA rules. AVOID unless property is in resort rental program.",
        hoa_str_risk=True,
    ),

    # ── LAKE NC ───────────────────────────────────────────────────────────────

    MarketSnapshot(
        market_id="nc_lake_norman_meck",
        name="Lake Norman",
        state="NC",
        category=MarketCategory.LAKE_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.57,
        peak_occupancy_rate=0.78,
        shoulder_occupancy_rate=0.58,
        offseason_occupancy_rate=0.34,
        median_adr_3bd=240.0,
        adr_yoy_growth=0.04,
        annual_revpan=121.0,
        active_listings=1600,
        listings_yoy_growth=0.12,
        median_home_price=650_000,
        home_price_yoy_appreciation=0.04,
        nearest_airport_code="CLT",
        nearest_airport_drive_min=30,
        beach_access_tier=4,
        golf_courses_30mi=16,
        regulatory_status=RegulatoryStatus.EVOLVING_BENIGN,
        regulatory_notes="Cornelius and Davidson have STR permit requirements. County areas unregulated. No ban proposals active.",
        hoa_str_risk=True,   # Many Lake Norman communities have HOAs with STR rules
    ),

    MarketSnapshot(
        market_id="nc_lake_lure_rutherford",
        name="Lake Lure / Chimney Rock",
        state="NC",
        category=MarketCategory.LAKE_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.55,
        peak_occupancy_rate=0.76,
        shoulder_occupancy_rate=0.56,
        offseason_occupancy_rate=0.30,
        median_adr_3bd=255.0,
        adr_yoy_growth=0.03,
        annual_revpan=122.0,
        active_listings=620,
        listings_yoy_growth=0.14,   # fast-growing small market post-Helene recovery
        median_home_price=430_000,
        home_price_yoy_appreciation=0.02,   # Hurricane Helene impacted 2024 values
        nearest_airport_code="AVL",
        nearest_airport_drive_min=48,
        beach_access_tier=4,
        golf_courses_30mi=5,
        # NOTE: Hurricane Helene (Sep 2024) caused significant damage to the Lake Lure
        # area. Recovery is underway but market uncertainty remains elevated.
        regulatory_status=RegulatoryStatus.EVOLVING_BENIGN,
        regulatory_notes="Town of Lake Lure STR-permissive. NOTE: Hurricane Helene (Sep 2024) caused major damage; market in recovery. Evaluate individual property flood/wind risk carefully.",
        hoa_str_risk=False,
    ),

    # ── MOUNTAIN NC ───────────────────────────────────────────────────────────

    MarketSnapshot(
        market_id="nc_asheville_buncombe",
        name="Asheville",
        state="NC",
        category=MarketCategory.MOUNTAIN_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.66,
        peak_occupancy_rate=0.82,
        shoulder_occupancy_rate=0.68,
        offseason_occupancy_rate=0.46,
        median_adr_3bd=265.0,
        adr_yoy_growth=0.01,    # slowing — regulatory uncertainty dampening growth
        annual_revpan=153.0,
        active_listings=2800,
        listings_yoy_growth=-0.08,   # supply shrinking due to regulation
        median_home_price=520_000,
        home_price_yoy_appreciation=0.02,
        nearest_airport_code="AVL",
        nearest_airport_drive_min=15,
        beach_access_tier=5,
        golf_courses_30mi=9,
        # MAJOR REGULATORY RISK: Asheville City Council enacted owner-occupancy
        # requirement for STR in residential zones. Non-owner-occupied STR
        # permits are no longer issued inside city limits.
        regulatory_status=RegulatoryStatus.EVOLVING_RISKY,
        regulatory_notes="ALERT: Asheville requires owner-occupancy for STR permits in residential zones (enacted 2022, expanded 2024). Non-owner STR inside city = regulatory violation. Rural Buncombe County remains permissive.",
        hoa_str_risk=False,
    ),

    MarketSnapshot(
        market_id="nc_boone_watauga",
        name="Boone / Banner Elk / Blowing Rock",
        state="NC",
        category=MarketCategory.MOUNTAIN_NC,
        data_date="2025-03-01",
        data_source="seed_2025q1",
        annual_occupancy_rate=0.60,
        peak_occupancy_rate=0.80,
        shoulder_occupancy_rate=0.62,
        offseason_occupancy_rate=0.36,
        median_adr_3bd=280.0,
        adr_yoy_growth=0.04,
        annual_revpan=148.0,
        active_listings=1900,
        listings_yoy_growth=0.09,
        median_home_price=495_000,
        home_price_yoy_appreciation=0.04,
        # TRI (Tri-Cities, TN) is ~75 min; AVL is ~1.5hr. Remote for guests.
        nearest_airport_code="TRI",
        nearest_airport_drive_min=75,
        beach_access_tier=5,
        golf_courses_30mi=7,
        regulatory_status=RegulatoryStatus.STABLE,
        regulatory_notes="Watauga and Avery Counties are STR-permissive. Boone town limits have registration requirement but no ban proposals. Ashe County unregulated.",
        hoa_str_risk=False,
    ),
]

# Quick-access dict
MARKETS_BY_ID: dict[str, MarketSnapshot] = {m.market_id: m for m in MARKETS}
