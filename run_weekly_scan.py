"""
Weekly scan orchestrator.

Run locally:  python run_weekly_scan.py
Run via CI:   GitHub Actions calls this on a schedule.

Writes:
  data/weekly_report.json   — latest scan (dashboard reads this)
  data/scan_history/YYYY-MM-DD.json — timestamped archive

Listing source selection (automatic):
  - If RAPIDAPI_KEY is set in .env → uses live Zillow listings
  - Otherwise                      → uses seeded example data
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from real_estate_agent.scoring.markets import MARKETS
from real_estate_agent.scoring.scorer import rank_markets
from real_estate_agent.properties.sources.seed import SeedSource
from real_estate_agent.properties.ranker import run_pipeline
from real_estate_agent.alerts.monitor import run_monitor
from real_estate_agent.alerts.seed_data import SEED_ARTICLES, build_prior_snapshots

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_REPORT_PATH = os.path.join(_DATA_DIR, "weekly_report.json")
_HISTORY_DIR = os.path.join(_DATA_DIR, "scan_history")


def _serialize_alert(a) -> dict:
    return {
        "alert_id": a.alert_id,
        "severity": a.severity.value,
        "alert_type": a.alert_type.value,
        "market_name": a.market_name,
        "title": a.title,
        "body": a.body,
        "action_required": a.action_required,
        "triggered_at": a.triggered_at,
        "url": a.url,
        "is_new": a.is_new,
        "positive": a.positive,
        "metric_label": a.metric_label,
        "metric_before": a.metric_before,
        "metric_after": a.metric_after,
    }


def _serialize_factor(f) -> dict:
    return {
        "name": f.name,
        "score": round(f.score, 1),
        "weight": f.weight,
        "weighted": round(f.weighted, 2),
        "note": f.note,
    }


def run(scan_date: str | None = None, email_address: str = "") -> dict:
    scan_date = scan_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── 1. Market scoring ────────────────────────────────────────────────────
    market_scores = rank_markets(MARKETS)

    markets_payload = [
        {
            "rank": ms.rank,
            "market_id": ms.market.market_id,
            "name": ms.market.name,
            "state": ms.market.state,
            "category": ms.market.category.value,
            "composite_score": ms.composite_score,
            "prior_composite": ms.prior_composite,
            "delta": round(ms.delta, 1) if ms.delta is not None else None,
            "annual_occupancy_rate": ms.market.annual_occupancy_rate,
            "peak_occupancy_rate": ms.market.peak_occupancy_rate,
            "median_adr_3bd": ms.market.median_adr_3bd,
            "adr_yoy_growth": ms.market.adr_yoy_growth,
            "annual_revpan": ms.market.annual_revpan,
            "active_listings": ms.market.active_listings,
            "listings_yoy_growth": ms.market.listings_yoy_growth,
            "median_home_price": ms.market.median_home_price,
            "home_price_yoy_appreciation": ms.market.home_price_yoy_appreciation,
            "nearest_airport_code": ms.market.nearest_airport_code,
            "nearest_airport_drive_min": ms.market.nearest_airport_drive_min,
            "beach_access_tier": ms.market.beach_access_tier,
            "golf_courses_30mi": ms.market.golf_courses_30mi,
            "regulatory_status": ms.market.regulatory_status.value,
            "regulatory_notes": ms.market.regulatory_notes,
            "regulatory_alert": ms.regulatory_alert,
            "viable_for_cash_purchase": ms.viable_for_cash_purchase,
            "viable_for_financed_purchase": ms.viable_for_financed_purchase,
            "factors": [_serialize_factor(f) for f in ms.factors],
        }
        for ms in market_scores
    ]

    # ── 2. Property pipeline ─────────────────────────────────────────────────
    rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
    if rapidapi_key:
        from real_estate_agent.properties.sources.zillow import ZillowSource
        sources = [ZillowSource(api_key=rapidapi_key)]
        source_label = "Zillow (live)"
        print("  Using live Zillow listings via RapidAPI")
    else:
        sources = [SeedSource()]
        source_label = "seed data (no RAPIDAPI_KEY set)"
        print("  No RAPIDAPI_KEY found — using seeded example data")

    passed, rejected = run_pipeline(sources, personal_use_weeks=4)

    properties_payload = {
        "passed": [
            {
                "rank": ps.rank,
                "listing_id": ps.listing.listing_id,
                "address": ps.listing.address,
                "city": ps.listing.city,
                "state": ps.listing.state,
                "zip_code": ps.listing.zip_code,
                "market_id": ps.listing.market_id,
                "price": ps.listing.price,
                "bedrooms": ps.listing.bedrooms,
                "bathrooms": ps.listing.bathrooms,
                "sqft": ps.listing.sqft,
                "year_built": ps.listing.year_built,
                "renovation_year": ps.listing.renovation_year,
                "property_type": ps.listing.property_type,
                "has_hoa": ps.listing.has_hoa,
                "hoa_monthly": ps.listing.hoa_monthly,
                "has_pool": ps.listing.has_pool,
                "beach_distance_miles": ps.listing.beach_distance_miles,
                "flood_zone": ps.listing.flood_zone,
                "airport_code": ps.listing.airport_code,
                "airport_drive_min": ps.listing.airport_drive_min,
                "days_on_market": ps.listing.days_on_market,
                "original_list_price": ps.listing.original_list_price,
                "price_reduction": ps.listing.price_reduction,
                "composite_score": ps.composite_score,
                "recommendation": ps.recommendation,
                "estimated_egi_annual": ps.listing.estimated_egi_annual,
                "estimated_monthly_cf_cash": ps.listing.estimated_monthly_cf_cash,
                "estimated_monthly_cf_dscr": ps.listing.estimated_monthly_cf_dscr,
                "estimated_irr_cash_5yr": ps.listing.estimated_irr_cash_5yr,
                "url": ps.listing.url,
                "factors": [_serialize_factor(f) for f in ps.factors],
            }
            for ps in passed
        ],
        "rejected": [
            {
                "listing_id": listing.listing_id,
                "address": listing.address,
                "city": listing.city,
                "state": listing.state,
                "price": listing.price,
                "url": listing.url,
                "failed_reasons": fr.failed_reasons,
            }
            for listing, fr in rejected
        ],
    }

    # ── 3. Alert monitor ─────────────────────────────────────────────────────
    prior_snapshots = build_prior_snapshots()
    alert_result = run_monitor(
        current_snapshots=MARKETS,
        prior_snapshots=prior_snapshots,
        news_articles=SEED_ARTICLES,
        scan_date=scan_date,
        commit_to_history=True,
        email_address=email_address or os.getenv("ALERT_TO_EMAIL", ""),
    )

    alerts_payload = {
        "immediate": [_serialize_alert(a) for a in alert_result["immediate"]],
        "weekly": [_serialize_alert(a) for a in alert_result["weekly"]],
        "all": [_serialize_alert(a) for a in alert_result["all"]],
    }

    new_alerts = [a for a in alert_result["all"] if a.is_new]

    # ── 4. Assemble report ───────────────────────────────────────────────────
    report = {
        "scan_date": scan_date,
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "markets_scored": len(market_scores),
            "properties_scanned": len(passed) + len(rejected),
            "properties_passed": len(passed),
            "properties_rejected": len(rejected),
            "alerts_total": len(alert_result["all"]),
            "alerts_new": len(new_alerts),
            "alerts_immediate": len(alert_result["immediate"]),
            "listing_source": source_label,
        },
        "markets": markets_payload,
        "properties": properties_payload,
        "alerts": alerts_payload,
    }

    # ── 5. Write output ───────────────────────────────────────────────────────
    os.makedirs(_DATA_DIR, exist_ok=True)
    os.makedirs(_HISTORY_DIR, exist_ok=True)

    with open(_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    archive_path = os.path.join(_HISTORY_DIR, f"{scan_date}.json")
    with open(archive_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = run()
    s = report["summary"]
    print(f"\n  ✓ Weekly scan complete  ·  {report['scan_date']}")
    print(f"  Markets scored:     {s['markets_scored']}")
    print(f"  Properties passed:  {s['properties_passed']} / {s['properties_scanned']} scanned")
    print(f"  New alerts:         {s['alerts_new']}  ({s['alerts_immediate']} immediate)")
    print(f"  Report written →    data/weekly_report.json")
    print(f"  Archive →           data/scan_history/{report['scan_date']}.json\n")
