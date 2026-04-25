"""
Full pipeline: fetch → filter → enrich → score → rank.
Orchestrates all modules into the weekly property scan.
"""

from __future__ import annotations

from real_estate_agent.scoring.markets import MARKETS_BY_ID
from real_estate_agent.scoring.scorer import score_market

from .models import PropertyListing, PropertyScore, FilterResult
from .filters import apply_filters
from .enrichment import enrich
from .scorer import score_property, recommendation, WEIGHTS
from .sources.base import ListingSource


def run_pipeline(
    sources: list[ListingSource],
    market_ids: list[str] | None = None,
    personal_use_weeks: int = 4,
) -> tuple[list[PropertyScore], list[tuple[PropertyListing, FilterResult]]]:
    """
    Returns:
        passed  — ranked PropertyScore list (best first)
        rejected — (listing, filter_result) pairs that failed hard filters
    """
    # Pre-build scored market map
    market_scores = {m.market_id: score_market(m) for m in MARKETS_BY_ID.values()}

    # 1. Fetch from all sources
    raw: list[PropertyListing] = []
    for source in sources:
        raw.extend(source.fetch(market_ids))

    # Deduplicate by listing_id
    seen: set[str] = set()
    listings: list[PropertyListing] = []
    for l in raw:
        if l.listing_id not in seen:
            seen.add(l.listing_id)
            listings.append(l)

    passed: list[PropertyScore] = []
    rejected: list[tuple[PropertyListing, FilterResult]] = []

    for listing in listings:
        # Resolve market snapshot
        snapshot = MARKETS_BY_ID.get(listing.market_id)
        if snapshot is None:
            fr = FilterResult(passed=False, failed_reasons=[f"Unknown market_id: {listing.market_id}"])
            rejected.append((listing, fr))
            continue

        # 2. Hard filter
        fr = apply_filters(listing, snapshot)
        if not fr.passed:
            rejected.append((listing, fr))
            continue

        # 3. Enrich with financial model
        enrich(listing, snapshot, personal_use_weeks)

        # 4. Score
        ms = market_scores.get(listing.market_id)
        factors = score_property(listing, ms)
        composite = sum(f.weighted for f in factors)

        ps = PropertyScore(
            listing=listing,
            filter_result=fr,
            factors=factors,
            composite_score=round(composite, 1),
            recommendation=recommendation(composite),
        )
        passed.append(ps)

    # 5. Rank
    passed.sort(key=lambda x: x.composite_score, reverse=True)
    for i, ps in enumerate(passed):
        ps.rank = i + 1

    return passed, rejected
