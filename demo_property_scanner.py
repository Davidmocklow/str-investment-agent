"""
Demo: Full weekly property scan pipeline.
  1. Fetch 22 seed listings across 8 NC/SC markets
  2. Apply hard filters
  3. Enrich each passer with financial model (cash + DSCR scenarios)
  4. Score and rank all passed properties
  5. Print leaderboard, detail cards for top 5, and rejection log
"""

from real_estate_agent.properties.sources.seed import SeedSource
from real_estate_agent.properties.ranker import run_pipeline
from real_estate_agent.properties.report import (
    print_property_table, print_property_detail, print_rejected,
)


if __name__ == "__main__":
    sources = [SeedSource()]

    passed, rejected = run_pipeline(sources, personal_use_weeks=4)

    # Full ranked table
    print_property_table(passed, title="WEEKLY PROPERTY PICKS  —  NC/SC STR INVESTMENT SCAN")

    # Top 5 detailed cards
    print("\n" + "=" * 74)
    print("  TOP 5 PROPERTIES — DETAILED BREAKDOWN")
    print("=" * 74)
    for ps in passed[:5]:
        print_property_detail(ps)

    # Rejection log
    print_rejected(rejected)

    print(f"  Scan complete:  {len(passed)} properties passed  |  {len(rejected)} filtered out")
    print(f"  Data source:    seeded Q1 2025 market data")
    print(f"  Next step:      connect Zillow / Realtor.com APIs for live listings\n")
