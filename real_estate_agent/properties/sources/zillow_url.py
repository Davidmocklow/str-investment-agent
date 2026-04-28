"""
Zillow single-property lookup via the private-zillow RapidAPI.

Used by the dashboard "Analyze a Property" feature.
The user pastes any Zillow listing URL → we fetch details and run the full
financial model + scoring pipeline on that specific property.

API: https://rapidapi.com/private-zillow/api/private-zillow
Endpoint: GET /byurl?url=<zillow_listing_url>
Auth: x-rapidapi-key header
"""

from __future__ import annotations

import math
import os
import re
from typing import Any

import requests

from real_estate_agent.properties.models import PropertyListing
from real_estate_agent.scoring.markets import MARKETS_BY_ID
from real_estate_agent.scoring.models import MarketSnapshot

_API_HOST = "private-zillow.p.rapidapi.com"
_API_BASE = f"https://{_API_HOST}"

# ── Market detection ──────────────────────────────────────────────────────────
# Maps city names and zip code prefixes to our tracked market IDs.

_CITY_TO_MARKET: dict[str, str] = {
    # OBX / Dare County
    "kill devil hills":    "nc_obx_dare",
    "nags head":           "nc_obx_dare",
    "kitty hawk":          "nc_obx_dare",
    "duck":                "nc_obx_dare",
    "southern shores":     "nc_obx_dare",
    "manteo":              "nc_obx_dare",
    "corolla":             "nc_obx_dare",
    # Crystal Coast
    "emerald isle":        "nc_crystal_coast_carteret",
    "atlantic beach":      "nc_crystal_coast_carteret",
    "pine knoll shores":   "nc_crystal_coast_carteret",
    "indian beach":        "nc_crystal_coast_carteret",
    "morehead city":       "nc_crystal_coast_carteret",
    "beaufort":            "nc_crystal_coast_carteret",
    # Wilmington
    "wrightsville beach":  "nc_wilmington_nhc",
    "carolina beach":      "nc_wilmington_nhc",
    "kure beach":          "nc_wilmington_nhc",
    "wilmington":          "nc_wilmington_nhc",
    # Topsail
    "surf city":           "nc_topsail_pender",
    "topsail beach":       "nc_topsail_pender",
    "north topsail beach": "nc_topsail_pender",
    "hampstead":           "nc_topsail_pender",
    # Hilton Head
    "hilton head island":  "sc_hilton_head_beaufort",
    "bluffton":            "sc_hilton_head_beaufort",
    "daufuskie island":    "sc_hilton_head_beaufort",
    # Isle of Palms
    "isle of palms":       "sc_isle_of_palms_charleston",
    "sullivan's island":   "sc_isle_of_palms_charleston",
    "sullivans island":    "sc_isle_of_palms_charleston",
    # Pawleys Island
    "pawleys island":      "sc_pawleys_georgetown",
    "litchfield beach":    "sc_pawleys_georgetown",
    "murrells inlet":      "sc_pawleys_georgetown",
    # Myrtle Beach
    "myrtle beach":        "sc_myrtle_beach_horry",
    "north myrtle beach":  "sc_myrtle_beach_horry",
    "surfside beach":      "sc_myrtle_beach_horry",
    "garden city beach":   "sc_myrtle_beach_horry",
    "conway":              "sc_myrtle_beach_horry",
    # Kiawah
    "kiawah island":       "sc_kiawah_charleston",
    "johns island":        "sc_kiawah_charleston",
    # Lake Norman
    "lake norman":         "nc_lake_norman_iredell",
    "mooresville":         "nc_lake_norman_iredell",
    "davidson":            "nc_lake_norman_iredell",
    "cornelius":           "nc_lake_norman_iredell",
    "denver":              "nc_lake_norman_iredell",
    # Lake Lure
    "lake lure":           "nc_lake_lure_rutherford",
    "chimney rock":        "nc_lake_lure_rutherford",
    # Asheville
    "asheville":           "nc_asheville_buncombe",
    "weaverville":         "nc_asheville_buncombe",
    "black mountain":      "nc_asheville_buncombe",
    "swannanoa":           "nc_asheville_buncombe",
    # Boone
    "boone":               "nc_boone_watauga",
    "blowing rock":        "nc_boone_watauga",
    "banner elk":          "nc_boone_watauga",
}

# Known airport info per market for properties in tracked markets
_MARKET_AIRPORT: dict[str, tuple[str, int]] = {
    "nc_obx_dare":                ("ORF", 78),
    "nc_crystal_coast_carteret":  ("EWN", 35),
    "nc_wilmington_nhc":          ("ILM", 14),
    "nc_topsail_pender":          ("ILM", 45),
    "sc_hilton_head_beaufort":    ("HHH", 12),
    "sc_isle_of_palms_charleston":("CHS", 32),
    "sc_pawleys_georgetown":      ("MYR", 28),
    "sc_myrtle_beach_horry":      ("MYR", 10),
    "sc_kiawah_charleston":       ("CHS", 45),
    "nc_lake_norman_iredell":     ("CLT", 35),
    "nc_lake_lure_rutherford":    ("AVL", 55),
    "nc_asheville_buncombe":      ("AVL", 18),
    "nc_boone_watauga":           ("CLT", 100),
}

# Beach reference coordinates per market (for distance calculation)
_MARKET_BEACH: dict[str, tuple[float, float] | None] = {
    "nc_obx_dare":                (35.9835, -75.6266),
    "nc_crystal_coast_carteret":  (34.6590, -76.9441),
    "nc_wilmington_nhc":          (34.2089, -77.7969),
    "nc_topsail_pender":          (34.4282, -77.5877),
    "sc_hilton_head_beaufort":    (32.1649, -80.7418),
    "sc_isle_of_palms_charleston":(32.7887, -79.7687),
    "sc_pawleys_georgetown":      (33.4501, -79.1228),
    "sc_myrtle_beach_horry":      (33.6891, -78.8867),
    "sc_kiawah_charleston":       (32.6082, -80.0886),
    "nc_lake_norman_iredell":     None,
    "nc_lake_lure_rutherford":    None,
    "nc_asheville_buncombe":      None,
    "nc_boone_watauga":           None,
}


def detect_market(city: str, state: str) -> str | None:
    """Return market_id for a given city/state, or None if not a tracked market."""
    return _CITY_TO_MARKET.get(city.lower().strip())


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _flood_zone_estimate(beach_dist: float | None) -> str:
    if beach_dist is None:
        return "X"
    if beach_dist <= 0.2:
        return "VE"
    if beach_dist <= 2.0:
        return "AE"
    return "X"


def _get(d: dict, *keys: str, default: Any = None) -> Any:
    """Safe nested dict getter."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, {})
    return d if d != {} else default


def lookup_by_url(zillow_url: str, api_key: str) -> tuple[PropertyListing | None, str | None]:
    """
    Fetch a single Zillow listing by URL and return a PropertyListing.

    Returns:
        (PropertyListing, None)   on success
        (None, error_message)     on failure
    """
    if not api_key:
        return None, "No API key provided. Add RAPIDAPI_KEY to your .env file."

    try:
        resp = requests.get(
            f"{_API_BASE}/byurl",
            headers={
                "x-rapidapi-host": _API_HOST,
                "x-rapidapi-key":  api_key,
                "Content-Type":    "application/json",
            },
            params={"url": zillow_url},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            return None, "API key not subscribed to private-zillow. Go to RapidAPI and subscribe (free tier)."
        return None, f"API error: {e}"
    except Exception as e:
        return None, f"Request failed: {e}"

    if "message" in data:
        return None, f"API returned: {data['message']}"

    try:
        listing = _parse(data, zillow_url)
        return listing, None
    except Exception as e:
        return None, f"Could not parse API response: {e}\n\nRaw keys returned: {list(data.keys())}"


def _parse(data: dict, original_url: str) -> PropertyListing:
    """Map raw private-zillow API response to PropertyListing."""

    # ── Address ───────────────────────────────────────────────────────────────
    # Handle different field name styles across Zillow API variants
    street   = (data.get("streetAddress") or data.get("address", {}).get("streetAddress")
                or data.get("address") or "Unknown")
    city     = (data.get("city") or _get(data, "address", "city") or "")
    state    = (data.get("state") or _get(data, "address", "state") or "")
    zip_code = (data.get("zipcode") or data.get("zipCode")
                or _get(data, "address", "zipcode") or "")

    # ── Core specs ────────────────────────────────────────────────────────────
    price    = float(data.get("price") or data.get("listPrice") or 0)
    bedrooms = int(data.get("bedrooms") or 0)
    baths    = float(data.get("bathrooms") or data.get("bathroomsFull") or 0)
    sqft     = int(data.get("livingArea") or data.get("squareFootage") or 0)
    yr_built = int(data.get("yearBuilt") or 0)

    home_type_raw = data.get("homeType") or data.get("propertyType") or "SINGLE_FAMILY"
    _type_map = {
        "SINGLE_FAMILY": "single_family", "Single Family": "single_family",
        "CONDO": "condo",                 "Condo": "condo",
        "TOWNHOUSE": "townhouse",          "Townhouse": "townhouse",
    }
    prop_type = _type_map.get(home_type_raw, "single_family")

    # ── HOA ───────────────────────────────────────────────────────────────────
    reso = data.get("resoFacts") or {}
    hoa_raw = (reso.get("hoaFee") or data.get("monthlyHoaFee")
               or _get(data, "hoa", "fee"))
    hoa_monthly = 0.0
    has_hoa = False
    if hoa_raw:
        try:
            hoa_monthly = float(str(hoa_raw).replace("$", "").replace(",", "").strip())
            has_hoa = hoa_monthly > 0
        except (ValueError, TypeError):
            pass

    # STR permission hints from description
    description = data.get("description") or ""
    _ok  = re.compile(r"vacation rental|short.term rental|str permitted|airbnb|vrbo|rental income", re.I)
    _ban = re.compile(r"no.short.term|no.vacation rental|no.str|no.airbnb|no rental|owner.occupied only", re.I)
    if has_hoa and description:
        hoa_str_permitted: bool | None = (
            True  if _ok.search(description)  else
            False if _ban.search(description) else
            None
        )
    else:
        hoa_str_permitted = None

    # ── Pool ──────────────────────────────────────────────────────────────────
    has_pool = bool(
        reso.get("hasPool")
        or data.get("hasPool")
        or _get(data, "features", "pool")
        or "pool" in description.lower()
    )

    # ── Geography ─────────────────────────────────────────────────────────────
    lat = data.get("latitude") or _get(data, "address", "latitude")
    lon = data.get("longitude") or _get(data, "address", "longitude")

    # Market detection
    market_id = detect_market(city, state)

    # Beach distance
    beach_dist: float | None = None
    if lat and lon and market_id:
        beach_ref = _MARKET_BEACH.get(market_id)
        if beach_ref:
            beach_dist = round(_haversine_miles(float(lat), float(lon), *beach_ref), 2)

    flood_zone = _flood_zone_estimate(beach_dist)

    # Airport
    airport_code, airport_drive_min = "?", 999
    if market_id and market_id in _MARKET_AIRPORT:
        airport_code, airport_drive_min = _MARKET_AIRPORT[market_id]

    # ── Listing signals ───────────────────────────────────────────────────────
    dom = int(data.get("daysOnZillow") or data.get("daysOnMarket") or 0)

    # Price history → original list price
    price_history = data.get("priceHistory") or []
    original_price = price
    for event in (price_history if isinstance(price_history, list) else []):
        if isinstance(event, dict) and "listed" in str(event.get("event") or "").lower():
            try:
                original_price = float(event["price"])
            except (KeyError, ValueError, TypeError):
                pass
            break
    price_reduction = max(0.0, original_price - price)

    # ── URL ───────────────────────────────────────────────────────────────────
    detail_url = data.get("url") or data.get("hdpUrl") or original_url
    if detail_url and not detail_url.startswith("http"):
        detail_url = f"https://www.zillow.com{detail_url}"

    # ── Fallback market_id if outside tracked markets ─────────────────────────
    if not market_id:
        # Use closest coastal NC market as a generic fallback so the model runs
        market_id = "nc_crystal_coast_carteret"

    zpid = str(data.get("zpid") or "unknown")

    return PropertyListing(
        listing_id=f"zillow_{zpid}",
        source="zillow_url",
        url=detail_url,
        address=street,
        city=city,
        state=state,
        zip_code=zip_code,
        market_id=market_id,
        price=price,
        bedrooms=bedrooms,
        bathrooms=baths,
        sqft=sqft,
        year_built=yr_built,
        property_type=prop_type,
        has_hoa=has_hoa,
        hoa_monthly=hoa_monthly,
        hoa_str_permitted=hoa_str_permitted,
        has_pool=has_pool,
        beach_distance_miles=beach_dist,
        airport_code=airport_code,
        airport_drive_min=airport_drive_min,
        flood_zone=flood_zone,
        days_on_market=dom,
        original_list_price=original_price,
        price_reduction=price_reduction,
    )
