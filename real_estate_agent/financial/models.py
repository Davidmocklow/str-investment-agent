from dataclasses import dataclass, field
from enum import Enum


class FinancingType(str, Enum):
    DSCR = "dscr"
    PORTFOLIO = "portfolio"
    CASH = "cash"


class MarketType(str, Enum):
    COASTAL_NC = "coastal_nc"
    COASTAL_SC = "coastal_sc"
    LAKE_NC = "lake_nc"
    MOUNTAIN_NC = "mountain_nc"


@dataclass
class PropertyInputs:
    purchase_price: float
    market_type: MarketType = MarketType.COASTAL_NC
    bedrooms: int = 3
    has_pool: bool = False
    has_hoa: bool = False
    hoa_monthly: float = 0.0
    property_age_years: int = 10


@dataclass
class MarketInputs:
    # Seasonal average daily rates
    peak_adr: float        # Jun–Aug
    shoulder_adr: float    # Apr–May, Sep–Oct
    offseason_adr: float   # Nov–Mar

    # Seasonal occupancy rates (as decimals)
    peak_occupancy: float = 0.87
    shoulder_occupancy: float = 0.68
    offseason_occupancy: float = 0.42

    # Fees and taxes (as decimals)
    pm_commission_rate: float = 0.25      # 25% typical coastal NC/SC
    platform_fee_rate: float = 0.035      # blended Airbnb + VRBO
    occupancy_tax_rate: float = 0.085     # collected from guests, remitted to county
    property_tax_rate: float = 0.007      # assessed annually on purchase price

    # Growth assumptions
    annual_appreciation_rate: float = 0.04   # 4% coastal NC/SC historical avg
    annual_adr_growth_rate: float = 0.03     # ADR grows 3%/yr


@dataclass
class FinancingInputs:
    financing_type: FinancingType
    down_payment: float
    interest_rate: float    # annual decimal (e.g. 0.0775 for 7.75%)
    loan_term_years: int = 30


@dataclass
class InsuranceInputs:
    homeowners_monthly: float = 300.0    # standard homeowners
    str_liability_monthly: float = 175.0  # STR/commercial liability rider
    windstorm_monthly: float = 0.0       # hurricane/windstorm rider (coastal only)
    flood_monthly: float = 80.0          # NFIP or private flood (zone-dependent)


@dataclass
class OperatingExpenseInputs:
    utilities_monthly: float = 450.0         # electric, water, internet, trash
    landscaping_monthly: float = 200.0
    cleaning_turnover_monthly: float = 200.0  # net costs not passed to guests
    maintenance_reserve_pct: float = 0.015    # 1.5% of purchase price/yr
    capex_reserve_pct: float = 0.010          # 1.0% of purchase price/yr
    str_licensing_annual: float = 500.0
    accounting_monthly: float = 150.0         # CPA + bookkeeping amortized


@dataclass
class ScenarioInputs:
    property: PropertyInputs
    market: MarketInputs
    financing: FinancingInputs
    insurance: InsuranceInputs = field(default_factory=InsuranceInputs)
    operating: OperatingExpenseInputs = field(default_factory=OperatingExpenseInputs)
    annual_personal_use_weeks: int = 4
    hold_period_years: int = 5
