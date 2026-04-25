"""
Normalizes raw metric values onto a 0–100 scale with optional inversion and
soft-clipping so extreme outliers don't dominate.
"""


def normalize(
    value: float,
    low: float,
    high: float,
    invert: bool = False,
    clip: bool = True,
) -> float:
    """
    Maps value linearly from [low, high] → [0, 100].

    invert=True  → lower value is better (e.g. supply growth, regulatory risk).
    clip=True    → clamps result to [0, 100] before returning.
    """
    if high == low:
        return 50.0
    score = (value - low) / (high - low) * 100.0
    if invert:
        score = 100.0 - score
    if clip:
        score = max(0.0, min(100.0, score))
    return score


def airport_score(drive_minutes: int) -> float:
    """Non-linear scoring — steep drop-off past 60 min (owner's hard preference)."""
    if drive_minutes <= 20:
        return 98.0
    if drive_minutes <= 30:
        return 90.0
    if drive_minutes <= 45:
        return 78.0
    if drive_minutes <= 60:
        return 65.0
    if drive_minutes <= 75:
        return 45.0
    if drive_minutes <= 90:
        return 28.0
    return 12.0


def beach_access_score(tier: int) -> float:
    """
    Tier 1 = oceanfront community     → 100
    Tier 2 = coastal, <5 mi to beach  → 80
    Tier 3 = coastal, 5–10 mi         → 60
    Tier 4 = lake / river              → 40
    Tier 5 = mountain, no water        → 20
    """
    return {1: 100.0, 2: 80.0, 3: 60.0, 4: 40.0, 5: 20.0}.get(tier, 20.0)


REGULATORY_SCORES = {
    "stable": 92.0,
    "evolving_benign": 68.0,
    "evolving_risky": 35.0,
    "restrictive": 10.0,
}
