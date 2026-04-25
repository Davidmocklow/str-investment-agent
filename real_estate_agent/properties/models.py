from __future__ import annotations

from dataclasses import dataclass, field
from real_estate_agent.scoring.models import MarketSnapshot


@dataclass
class PropertyListing:
    listing_id: str
    source: str            # "zillow", "realtor", "vrbo_airdna", "seed"
    url: str

    # Identity
    address: str
    city: str
    state: str
    zip_code: str
    market_id: str         # must match a MarketSnapshot.market_id

    # Core specs
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    year_built: int
    property_type: str     # "single_family", "condo", "townhouse"

    # HOA
    has_hoa: bool
    hoa_monthly: float
    hoa_str_permitted: bool | None  # None = unknown / not disclosed

    # Amenities
    has_pool: bool

    # Geography
    beach_distance_miles: float | None   # None = inland / no beach
    airport_code: str
    airport_drive_min: int
    flood_zone: str        # "X"=preferred, "AE"=moderate, "VE"=high coastal risk

    # Listing signals
    days_on_market: int
    original_list_price: float
    price_reduction: float   # cumulative price drop from original

    # Optional renovation year — allows relaxed age filter for substantially updated properties
    renovation_year: int | None = None

    # Enriched after scoring (None until enrich() is called)
    market_snapshot: MarketSnapshot | None = None
    estimated_egi_annual: float | None = None
    estimated_monthly_cf_cash: float | None = None
    estimated_monthly_cf_dscr: float | None = None
    estimated_irr_cash_5yr: float | None = None

    @property
    def age(self) -> int:
        return 2025 - self.year_built

    @property
    def effective_age(self) -> int:
        """Age since last major renovation, or full age if no renovation on record."""
        if self.renovation_year:
            return 2025 - self.renovation_year
        return self.age

    @property
    def price_reduction_pct(self) -> float:
        return self.price_reduction / self.original_list_price if self.original_list_price > 0 else 0.0

    @property
    def price_per_sqft(self) -> float:
        return self.price / self.sqft if self.sqft > 0 else 0.0


@dataclass
class FilterResult:
    passed: bool
    failed_reasons: list[str] = field(default_factory=list)


@dataclass
class FactorScore:
    name: str
    score: float      # 0–100
    weight: float
    weighted: float
    note: str = ""


@dataclass
class PropertyScore:
    listing: PropertyListing
    filter_result: FilterResult
    factors: list[FactorScore]
    composite_score: float
    rank: int = 0
    recommendation: str = ""

    @property
    def factor_map(self) -> dict[str, FactorScore]:
        return {f.name: f for f in self.factors}
