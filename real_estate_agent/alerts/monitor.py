"""
Alert monitor — full orchestration pipeline.

Run cadence:
  REGULATORY  → daily (news scanner + legislature RSS)
  MARKET      → weekly (snapshot comparison)
  WEATHER     → daily during hurricane season (Jun–Nov)

Each run:
  1. Collect alerts from all sources
  2. Deduplicate against history
  3. Sort by severity
  4. Deliver CRITICAL/HIGH immediately (console + file + email stub)
  5. Return all alerts for inclusion in weekly report
"""

from __future__ import annotations

from .models import Alert, AlertSeverity, IMMEDIATE_SEVERITIES
from .market_triggers import run_all_market_triggers
from .news_scanner import scan_articles
from .history import deduplicate, commit
from .delivery import deliver_console, write_notification_file, send_email
from real_estate_agent.scoring.models import MarketSnapshot


def run_monitor(
    current_snapshots: list[MarketSnapshot],
    prior_snapshots: dict[str, MarketSnapshot] | None,
    news_articles: list | None,
    scan_date: str = "2025-04-25",
    commit_to_history: bool = True,
    email_address: str = "",
) -> dict[str, list[Alert]]:
    """
    Runs all alert checks and delivers as appropriate.

    Returns:
        {
          "immediate":  alerts delivered right now (CRITICAL + HIGH, new only)
          "weekly":     alerts for weekly report bundle (MEDIUM + LOW)
          "all":        everything, including already-seen
        }
    """
    raw_alerts: list[Alert] = []

    # ── 1. Market condition triggers ─────────────────────────────────────────
    for snap in current_snapshots:
        prior = prior_snapshots.get(snap.market_id) if prior_snapshots else None
        market_alerts = run_all_market_triggers(snap, prior, date=scan_date)
        raw_alerts.extend(market_alerts)

    # ── 2. News / regulatory scanner ─────────────────────────────────────────
    if news_articles:
        news_alerts = scan_articles(news_articles)
        raw_alerts.extend(news_alerts)

    # ── 3. Deduplicate against history ────────────────────────────────────────
    alerts = deduplicate(raw_alerts)

    # ── 4. Sort: severity (CRITICAL first), then new-before-seen ─────────────
    sev_order = {
        AlertSeverity.CRITICAL: 0,
        AlertSeverity.HIGH:     1,
        AlertSeverity.MEDIUM:   2,
        AlertSeverity.LOW:      3,
    }
    alerts.sort(key=lambda a: (sev_order[a.severity], not a.is_new))

    # ── 5. Split by delivery cadence ─────────────────────────────────────────
    immediate = [a for a in alerts if a.severity in IMMEDIATE_SEVERITIES and a.is_new]
    weekly = [a for a in alerts if a.severity not in IMMEDIATE_SEVERITIES]

    # ── 6. Deliver ────────────────────────────────────────────────────────────
    if immediate:
        deliver_console(immediate, header="IMMEDIATE ALERTS  —  Action Required")
        write_notification_file(immediate)
        send_email(immediate, email_address)

    # ── 7. Commit new alerts to history ──────────────────────────────────────
    if commit_to_history:
        commit(alerts)

    return {"immediate": immediate, "weekly": weekly, "all": alerts}
