"""
Demo: Full alert monitor run.

Simulates a weekly scan that:
  - Detects regulatory changes from seeded news articles
  - Detects market condition threshold crossings (vs. prior week)
  - Delivers CRITICAL/HIGH alerts immediately
  - Bundles MEDIUM/LOW into the weekly report section
"""

from real_estate_agent.scoring.markets import MARKETS
from real_estate_agent.alerts.monitor import run_monitor
from real_estate_agent.alerts.delivery import deliver_console
from real_estate_agent.alerts.history import clear_history
from real_estate_agent.alerts.seed_data import SEED_ARTICLES, build_prior_snapshots

SCAN_DATE = "2025-04-25"


if __name__ == "__main__":
    # Clear history so all demo alerts appear as new
    clear_history()

    prior_snapshots = build_prior_snapshots()

    result = run_monitor(
        current_snapshots=MARKETS,
        prior_snapshots=prior_snapshots,
        news_articles=SEED_ARTICLES,
        scan_date=SCAN_DATE,
        commit_to_history=True,
        email_address="you@example.com",
    )

    # Weekly report section (MEDIUM + LOW)
    if result["weekly"]:
        deliver_console(result["weekly"], header="WEEKLY REPORT  —  Market Intelligence Alerts")

    # Summary
    all_alerts = result["all"]
    new_alerts = [a for a in all_alerts if a.is_new]
    print(f"  Alert scan complete  ·  {SCAN_DATE}")
    print(f"  Total:     {len(all_alerts)} alerts generated")
    print(f"  New:       {len(new_alerts)} new this week")
    print(f"  Immediate: {len(result['immediate'])} CRITICAL/HIGH delivered now")
    print(f"  Weekly:    {len(result['weekly'])} MEDIUM/LOW bundled in report")
    print(f"\n  Run again to see deduplication — all alerts will show as [seen]\n")
