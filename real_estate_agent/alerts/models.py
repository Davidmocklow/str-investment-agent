from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AlertType(str, Enum):
    # ── Regulatory ────────────────────────────────────────────────────────────
    REG_STR_BAN          = "reg_str_ban"           # enacted or imminent ban
    REG_BILL_INTRODUCED  = "reg_bill_introduced"   # bill filed in legislature
    REG_PERMIT_CHANGE    = "reg_permit_change"      # new/changed permit requirements
    REG_ZONING_CHANGE    = "reg_zoning_change"      # zoning amendment affecting STR
    REG_HOA_CHANGE       = "reg_hoa_change"         # HOA updates STR policy
    REG_PREEMPTION       = "reg_preemption"         # state preempts local bans (positive)
    REG_PERMIT_CAP       = "reg_permit_cap"         # cap on new STR permits reached

    # ── Market conditions ─────────────────────────────────────────────────────
    MKT_OCCUPANCY_DROP   = "mkt_occupancy_drop"    # significant occupancy decline
    MKT_ADR_DROP         = "mkt_adr_drop"          # ADR falling (reduce prices or investigate)
    MKT_ADR_SURGE        = "mkt_adr_surge"         # ADR rising (raise prices / sell signal)
    MKT_SUPPLY_SURGE     = "mkt_supply_surge"      # rapid new listing growth (competition)
    MKT_PRICE_SURGE      = "mkt_price_surge"       # home values appreciating fast (sell signal)
    MKT_PRICE_DROP       = "mkt_price_drop"        # home values softening

    # ── Weather / external ────────────────────────────────────────────────────
    WEATHER_MAJOR        = "weather_major"          # hurricane, major flooding
    WEATHER_WATCH        = "weather_watch"          # active storm watch/warning
    RECOVERY_UPDATE      = "recovery_update"        # post-disaster market update


class AlertSeverity(str, Enum):
    CRITICAL = "critical"   # immediate action required — delivered outside weekly report
    HIGH     = "high"       # review within 24 hours — also delivered immediately
    MEDIUM   = "medium"     # review in weekly report
    LOW      = "low"        # informational, weekly report only


# Severities that bypass the weekly report and get immediate delivery
IMMEDIATE_SEVERITIES = {AlertSeverity.CRITICAL, AlertSeverity.HIGH}


@dataclass
class Alert:
    alert_id: str                       # deterministic: "{market_id}_{type}_{date}"
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    body: str                           # detailed explanation
    action_required: str                # what the owner should do now
    triggered_at: str                   # ISO date string "2025-03-15"
    source: str                         # "market_trigger", "news_scanner", "seed", etc.
    market_id: str | None = None
    market_name: str | None = None
    url: str | None = None
    is_new: bool = True                 # False = already delivered (from history)
    positive: bool = False              # True = good news (appreciation, preemption)
    metric_label: str | None = None
    metric_before: float | None = None
    metric_after: float | None = None


@dataclass
class NewsArticle:
    """Represents a raw article fetched from a news source before classification."""
    article_id: str
    headline: str
    body_snippet: str
    source_name: str
    published_date: str     # ISO date
    url: str
    market_hint: str | None = None   # pre-tagged market_id if known
