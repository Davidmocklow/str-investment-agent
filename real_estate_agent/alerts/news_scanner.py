"""
Regulatory news scanner.

Classifies news articles by:
  1. Relevance to STR regulation (keyword matching)
  2. Sentiment (ban/restrict vs. permit/allow)
  3. Severity (enacted vs. proposed vs. informational)
  4. Market (which tracked market does it reference)

When real APIs are connected, feed NewsArticle objects from:
  - News API (newsapi.org) — search: "short-term rental {market_name}"
  - Google News RSS feeds for each county
  - NC General Assembly bill tracker RSS
  - SC Legislature bill tracker RSS
  - Municode change notifications
"""

from __future__ import annotations

import re
from .models import Alert, AlertType, AlertSeverity, NewsArticle
from real_estate_agent.scoring.markets import MARKETS_BY_ID

# ── Keyword taxonomy ──────────────────────────────────────────────────────────

_BAN_ENACTED = [
    "banned", "prohibited", "ban enacted", "ordinance passed", "vote approved",
    "council approved", "signed into law", "effective immediately",
    "no longer permitted", "cease and desist", "illegal to operate",
]
_BAN_PROPOSED = [
    "proposed ban", "ban proposed", "considering ban", "moratorium",
    "restrict short-term", "limit vacation rental", "bill introduced",
    "ordinance introduced", "first reading", "committee vote",
    "public hearing scheduled", "considering ordinance",
]
_PERMIT_CHANGE = [
    "new permit required", "permit cap", "license required", "registration required",
    "new fee", "annual renewal", "density cap", "cap on permits",
    "no new permits", "permit moratorium", "waitlist",
]
_PREEMPTION = [
    "state preempts", "preemption bill", "preempt local", "statewide rule",
    "override local ban", "state law supersedes", "freedom act",
    "municipalities cannot ban", "local bans prohibited",
]
_ZONING = [
    "zoning amendment", "rezoned", "conditional use permit", "overlay district",
    "residential zoning", "R-1 zoning", "owner-occupancy", "non-owner-occupied",
]
_WEATHER = [
    "hurricane", "tropical storm", "flooding", "storm surge", "evacuation order",
    "mandatory evacuation", "major damage", "state of emergency",
]
_MARKET_POSITIVE = [
    "record revenue", "occupancy high", "strong demand", "sold out summer",
    "highest rates", "peak season bookings",
]

_STR_CONTEXT = [
    "short-term rental", "vacation rental", "airbnb", "vrbo", "str",
    "nightly rental", "holiday rental",
]

# Market name aliases for matching (lowercase)
_MARKET_ALIASES: dict[str, list[str]] = {
    "nc_obx_dare":               ["outer banks", "dare county", "kill devil hills", "nags head", "corolla", "obx"],
    "nc_crystal_coast_carteret": ["crystal coast", "carteret county", "emerald isle", "atlantic beach", "morehead city"],
    "nc_wilmington_nhc":         ["wilmington", "wrightsville beach", "new hanover county"],
    "nc_topsail_pender":         ["topsail", "surf city", "pender county", "onslow county"],
    "sc_hilton_head_beaufort":   ["hilton head", "beaufort county", "bluffton", "hilton head island"],
    "sc_isle_of_palms_charleston": ["isle of palms", "iop", "sullivan's island", "charleston county"],
    "sc_pawleys_georgetown":     ["pawleys island", "litchfield", "georgetown county"],
    "sc_myrtle_beach_horry":     ["myrtle beach", "horry county", "grand strand", "north myrtle beach"],
    "sc_kiawah_charleston":      ["kiawah", "seabrook island"],
    "nc_lake_norman_meck":       ["lake norman", "cornelius", "davidson", "mecklenburg"],
    "nc_lake_lure_rutherford":   ["lake lure", "chimney rock", "rutherford county"],
    "nc_asheville_buncombe":     ["asheville", "buncombe county"],
    "nc_boone_watauga":          ["boone", "banner elk", "blowing rock", "watauga county", "avery county"],
}


def _contains_any(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)


def _detect_market(text: str) -> str | None:
    t = text.lower()
    for market_id, aliases in _MARKET_ALIASES.items():
        if any(alias in t for alias in aliases):
            return market_id
    return None


def _severity_from_language(text: str) -> AlertSeverity:
    if _contains_any(text, _BAN_ENACTED):
        return AlertSeverity.CRITICAL
    if _contains_any(text, _BAN_PROPOSED + _PERMIT_CHANGE + _PREEMPTION):
        return AlertSeverity.HIGH
    if _contains_any(text, _ZONING):
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def classify_article(article: NewsArticle) -> Alert | None:
    """
    Attempt to classify a NewsArticle into an Alert.
    Returns None if article is not STR-relevant.
    """
    full_text = f"{article.headline} {article.body_snippet}"

    if not _contains_any(full_text, _STR_CONTEXT):
        # Check for weather — doesn't need STR context
        if _contains_any(full_text, _WEATHER):
            market_id = article.market_hint or _detect_market(full_text)
            snapshot = MARKETS_BY_ID.get(market_id) if market_id else None
            return Alert(
                alert_id=f"news__{article.article_id}",
                alert_type=AlertType.WEATHER_MAJOR,
                severity=AlertSeverity.HIGH,
                market_id=market_id,
                market_name=snapshot.name if snapshot else "Unknown",
                title=f"Weather event: {article.headline[:80]}",
                body=article.body_snippet,
                action_required=(
                    "Check if tracked properties in this area have active bookings. "
                    "Notify property manager. Review cancellation policy."
                ),
                triggered_at=article.published_date,
                source=f"news:{article.source_name}",
                url=article.url,
            )
        return None

    market_id = article.market_hint or _detect_market(full_text)
    snapshot = MARKETS_BY_ID.get(market_id) if market_id else None
    market_name = snapshot.name if snapshot else "Multiple markets"

    # Classify by type
    if _contains_any(full_text, _PREEMPTION):
        atype = AlertType.REG_PREEMPTION
        positive = True
    elif _contains_any(full_text, _BAN_ENACTED + _BAN_PROPOSED):
        atype = AlertType.REG_STR_BAN
        positive = False
    elif _contains_any(full_text, _PERMIT_CHANGE):
        atype = AlertType.REG_PERMIT_CHANGE
        positive = False
    elif _contains_any(full_text, _ZONING):
        atype = AlertType.REG_ZONING_CHANGE
        positive = False
    else:
        return None  # STR-related but not regulatory — skip

    sev = _severity_from_language(full_text)

    action_map = {
        AlertType.REG_STR_BAN: (
            "Read the full ordinance text. Determine if existing permits are grandfathered. "
            "Consult a local real estate attorney before purchasing in this market."
        ),
        AlertType.REG_PERMIT_CHANGE: (
            "Note new permit requirements and fees. Verify if cap affects new purchases. "
            "If buying: confirm permit availability before closing."
        ),
        AlertType.REG_PREEMPTION: (
            "Track bill progress through legislature. If passed, removes a key risk from SC/NC markets. "
            "No immediate action required."
        ),
        AlertType.REG_ZONING_CHANGE: (
            "Identify which zones are affected. Verify any target property is in a permissive zone. "
            "Request zoning verification letter from county before purchase."
        ),
    }

    return Alert(
        alert_id=f"news__{article.article_id}",
        alert_type=atype,
        severity=sev,
        market_id=market_id,
        market_name=market_name,
        title=article.headline[:120],
        body=article.body_snippet,
        action_required=action_map.get(atype, "Review and monitor."),
        triggered_at=article.published_date,
        source=f"news:{article.source_name}",
        url=article.url,
        positive=positive if 'positive' in dir() else False,
    )


def scan_articles(articles: list[NewsArticle]) -> list[Alert]:
    """Classify all articles, returning only those that generated alerts."""
    alerts = []
    for article in articles:
        alert = classify_article(article)
        if alert:
            alerts.append(alert)
    return alerts
