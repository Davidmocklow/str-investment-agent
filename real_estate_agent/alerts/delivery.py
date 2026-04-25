"""
Alert delivery channels.

Console: always active (stdout).
Email:   stub — fill in SendGrid/SMTP credentials in .env to activate.
File:    writes a JSON notification file the dashboard can poll.

Delivery is split by cadence:
  IMMEDIATE  (CRITICAL + HIGH)  → delivered as soon as generated, outside weekly report
  WEEKLY     (MEDIUM + LOW)     → bundled into the weekly report section
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from .models import Alert, AlertSeverity, IMMEDIATE_SEVERITIES

_NOTIF_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "pending_notifications.json"
)


# ── Console delivery ──────────────────────────────────────────────────────────

_SEV_PREFIX = {
    AlertSeverity.CRITICAL: "🔴 CRITICAL",
    AlertSeverity.HIGH:     "🟠 HIGH    ",
    AlertSeverity.MEDIUM:   "🟡 MEDIUM  ",
    AlertSeverity.LOW:      "🔵 LOW     ",
}

_TYPE_SHORT = {
    "reg_str_ban":         "REG:BAN",
    "reg_bill_introduced": "REG:BILL",
    "reg_permit_change":   "REG:PERMIT",
    "reg_zoning_change":   "REG:ZONING",
    "reg_hoa_change":      "REG:HOA",
    "reg_preemption":      "REG:PREEMPT",
    "reg_permit_cap":      "REG:CAP",
    "mkt_occupancy_drop":  "MKT:OCC↓",
    "mkt_adr_drop":        "MKT:ADR↓",
    "mkt_adr_surge":       "MKT:ADR↑",
    "mkt_supply_surge":    "MKT:SUPPLY↑",
    "mkt_price_surge":     "MKT:PRICE↑",
    "mkt_price_drop":      "MKT:PRICE↓",
    "weather_major":       "WEATHER",
    "weather_watch":       "WEATHER",
    "recovery_update":     "RECOVERY",
}


def deliver_console(alerts: list[Alert], header: str = "ALERTS") -> None:
    if not alerts:
        return
    W = 80
    print(f"\n{'█' * W}")
    print(f"  {header}  ({len(alerts)} alert(s))")
    print(f"{'█' * W}")

    # Group by severity
    for sev in [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM, AlertSeverity.LOW]:
        group = [a for a in alerts if a.severity == sev]
        if not group:
            continue
        for alert in group:
            _print_alert(alert)

    print(f"{'█' * W}\n")


def _print_alert(alert: Alert) -> None:
    W = 78
    prefix = _SEV_PREFIX.get(alert.severity, "     ")
    atype = _TYPE_SHORT.get(alert.alert_type.value, alert.alert_type.value)
    new_tag = " [NEW]" if alert.is_new else " [seen]"
    pos_tag = " ✓ POSITIVE" if alert.positive else ""

    print(f"\n  {prefix}  [{atype}]{new_tag}{pos_tag}")
    print(f"  {'─' * W}")
    market_str = f"  Market: {alert.market_name}" if alert.market_name else "  Market: All tracked markets"
    print(f"{market_str}  |  {alert.triggered_at}")
    print(f"  {alert.title}")
    print()

    # Word-wrap body at 76 chars
    words = alert.body.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 78:
            print(line)
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)

    print(f"\n  Action: {alert.action_required}")
    if alert.url:
        print(f"  Source: {alert.url}")
    if alert.metric_before is not None and alert.metric_after is not None:
        print(f"  Metric: {alert.metric_label}  {alert.metric_before:.3g} → {alert.metric_after:.3g}")


# ── File-based notification (for dashboard polling) ───────────────────────────

def write_notification_file(alerts: list[Alert], path: str = _NOTIF_PATH) -> None:
    """Writes new immediate-severity alerts to a JSON file for dashboard pickup."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = [
        {
            "alert_id": a.alert_id,
            "severity": a.severity.value,
            "type": a.alert_type.value,
            "market": a.market_name,
            "title": a.title,
            "action": a.action_required,
            "date": a.triggered_at,
            "url": a.url,
            "positive": a.positive,
        }
        for a in alerts
        if a.is_new and a.severity in IMMEDIATE_SEVERITIES
    ]
    if payload:
        with open(path, "w") as f:
            json.dump({"generated_at": datetime.now().isoformat(), "alerts": payload}, f, indent=2)


# ── Email stub ─────────────────────────────────────────────────────────────────

def send_email(alerts: list[Alert], to_address: str = "") -> None:
    """
    Stub — replace with SendGrid or SMTP call.
    Template renders all CRITICAL/HIGH alerts into an HTML email.

    Required env vars (add to .env):
      SENDGRID_API_KEY=...
      ALERT_FROM_EMAIL=alerts@yourdomain.com
      ALERT_TO_EMAIL=you@example.com
    """
    immediate = [a for a in alerts if a.is_new and a.severity in IMMEDIATE_SEVERITIES]
    if not immediate:
        return
    # Placeholder — log intent
    print(f"\n  [EMAIL STUB] Would send {len(immediate)} CRITICAL/HIGH alert(s) to {to_address or '(ALERT_TO_EMAIL)'}")
    for a in immediate:
        print(f"    → {a.severity.value.upper()}: {a.title[:70]}")
