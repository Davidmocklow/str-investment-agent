from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MarketCategory(str, Enum):
    COASTAL_NC = "coastal_nc"
    COASTAL_SC = "coastal_sc"
    LAKE_NC = "lake_nc"
    MOUNTAIN_NC = "mountain_nc"


class RegulatoryStatus(str, Enum):
    STABLE = "stable"                   # clear rules, no active threats
    EVOLVING_BENIGN = "evolving_benign" # change underway, not hurting metrics
    EVOLVING_RISKY = "evolving_risky"   # change underway, metrics showing impact
    RESTRICTIVE = "restrictive"         # active bans or owner-occupancy requirements


@dataclass
class MarketSnapshot:
    """All raw data for a single market. Updated weekly via APIs (or seeded manually)."""

    market_id: str
    name: str
    state: str
    category: MarketCategory
    data_date: str          # ISO date this snapshot was generated
    data_source: str        # "seed_2025q1", "airdna_api", etc.

    # ── STR performance (AirDNA or equivalent) ──────────────────────────────
    annual_occupancy_rate: float       # blended annual, decimal
    peak_occupancy_rate: float         # Jun–Aug avg, decimal
    shoulder_occupancy_rate: float     # Apr–May / Sep–Oct avg
    offseason_occupancy_rate: float    # Nov–Mar avg
    median_adr_3bd: float              # median ADR for 3-bedroom STR
    adr_yoy_growth: float              # year-over-year ADR change, decimal
    annual_revpan: float               # revenue per available night (annualized avg)
    active_listings: int               # total active STR listings in market
    listings_yoy_growth: float         # supply growth rate, decimal

    # ── Property market (Zillow / Redfin) ───────────────────────────────────
    median_home_price: float           # for target property type/size
    home_price_yoy_appreciation: float # decimal

    # ── Geography ────────────────────────────────────────────────────────────
    nearest_airport_code: str
    nearest_airport_drive_min: int     # drive minutes to nearest commercial service
    beach_access_tier: int             # 1=oceanfront, 2=<5mi, 3=5-10mi, 4=lake, 5=mountain
    golf_courses_30mi: int             # count of golf courses within 30 miles

    # ── Regulatory ───────────────────────────────────────────────────────────
    regulatory_status: RegulatoryStatus
    regulatory_notes: str
    hoa_str_risk: bool                 # True if many properties have HOA STR bans

    # ── Optional: prior-week snapshot for delta calculation ─────────────────
    prior_composite_score: float | None = None


@dataclass
class FactorScore:
    name: str
    raw_value: float | str
    score: float          # 0–100
    weight: float
    weighted: float       # score × weight
    note: str = ""


@dataclass
class MarketScore:
    market: MarketSnapshot
    factors: list[FactorScore]
    composite_score: float    # 0–100 weighted sum
    rank: int = 0
    prior_composite: float | None = None
    delta: float | None = None          # composite change vs. prior week

    # Derived flags
    regulatory_alert: bool = False
    viable_for_cash_purchase: bool = False
    viable_for_financed_purchase: bool = False

    @property
    def factor_map(self) -> dict[str, FactorScore]:
        return {f.name: f for f in self.factors}
