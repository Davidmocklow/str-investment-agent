"""
Zillow listing source via RapidAPI (zillow-com1).

Setup:
  1. Create a free account at https://rapidapi.com
  2. Subscribe to "Zillow-com1" API (free tier: 100 req/mo, basic: $10/mo for 1,000 req)
     https://rapidapi.com/apimaker/api/zillow-com1
  3. Add to .env:  RAPIDAPI_KEY=your_key_here

API cost per weekly scan:
  - 1 search request per market location  (~15-20 markets × 2-4 searches = 30-60 req)
  - 1 detail request per property that passes price+beds pre-filter (~20-40 req)
  - Total: ~50-100 requests/week → Basic plan ($10/mo) is sufficient

Fields Zillow provides: price, beds, baths, sqft, year built, HOA fee, pool (via detail),
                        days on market, price history, lat/lng, address.
Fields we derive locally: beach distance (haversine from lat/lng), flood zone estimate,
                          airport drive time (market default), HOA STR permission.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from datetime import datetime, timezone

import requests

from real_estate_agent.properties.models import PropertyListing
from .base import ListingSource

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "zillow_cache")

# ── Market search configuration ────────────────────────────────────────────────
# Each market maps to one or more Zillow location strings to search,
# plus local geography facts we can't get from Zillow.

_MARKET_CONFIG: dict[str, dict] = {
    "nc_obx_dare": {
        "locations": ["Kill Devil Hills, NC", "Nags Head, NC", "Duck, NC", "Kitty Hawk, NC"],
        "airport_code": "ORF",
        "airport_drive_min": 78,
        "beach_coord": (35.9835, -75.6266),   # Kill Devil Hills beachfront
    },
    "nc_crystal_coast_carteret": {
        "locations": ["Emerald Isle, NC", "Atlantic Beach, NC", "Pine Knoll Shores, NC"],
        "airport_code": "EWN",
        "airport_drive_min": 35,
        "beach_coord": (34.6590, -76.9441),   # Emerald Isle beachfront
    },
    "nc_wilmington_nhc": {
        "locations": ["Wrightsville Beach, NC", "Carolina Beach, NC"],
        "airport_code": "ILM",
        "airport_drive_min": 14,
        "beach_coord": (34.2089, -77.7969),   # Wrightsville Beach
    },
    "nc_topsail_pender": {
        "locations": ["Surf City, NC", "Topsail Beach, NC", "North Topsail Beach, NC"],
        "airport_code": "ILM",
        "airport_drive_min": 45,
        "beach_coord": (34.4282, -77.5877),   # Surf City beachfront
    },
    "sc_hilton_head_beaufort": {
        "locations": ["Hilton Head Island, SC"],
        "airport_code": "HHH",
        "airport_drive_min": 12,
        "beach_coord": (32.1649, -80.7418),   # Coligny Beach, Hilton Head
    },
    "sc_isle_of_palms_charleston": {
        "locations": ["Isle of Palms, SC", "Sullivan's Island, SC"],
        "airport_code": "CHS",
        "airport_drive_min": 32,
        "beach_coord": (32.7887, -79.7687),   # Isle of Palms beachfront
    },
    "sc_pawleys_georgetown": {
        "locations": ["Pawleys Island, SC", "Litchfield Beach, SC"],
        "airport_code": "MYR",
        "airport_drive_min": 28,
        "beach_coord": (33.4501, -79.1228),   # Pawleys Island beachfront
    },
    "sc_myrtle_beach_horry": {
        "locations": ["Myrtle Beach, SC", "North Myrtle Beach, SC", "Surfside Beach, SC"],
        "airport_code": "MYR",
        "airport_drive_min": 10,
        "beach_coord": (33.6891, -78.8867),   # Myrtle Beach oceanfront
    },
    "nc_lake_norman_iredell": {
        "locations": ["Mooresville, NC", "Davidson, NC", "Cornelius, NC"],
        "airport_code": "CLT",
        "airport_drive_min": 35,
        "beach_coord": None,   # lake market — no beach
    },
    "nc_lake_lure_rutherford": {
        "locations": ["Lake Lure, NC", "Chimney Rock, NC"],
        "airport_code": "AVL",
        "airport_drive_min": 55,
        "beach_coord": None,
    },
    "nc_asheville_buncombe": {
        "locations": ["Asheville, NC", "Weaverville, NC", "Black Mountain, NC"],
        "airport_code": "AVL",
        "airport_drive_min": 18,
        "beach_coord": None,
    },
    "nc_boone_watauga": {
        "locations": ["Boone, NC", "Blowing Rock, NC"],
        "airport_code": "CLT",
        "airport_drive_min": 100,
        "beach_coord": None,
    },
}

# Keywords in listing description suggesting STR is permitted / banned
_STR_OK_WORDS = re.compile(
    r"vacation rental|short.term rental|str permitted|airbnb|vrbo|rental income|"
    r"investment property|rental history|currently renting|rental approved",
    re.IGNORECASE,
)
_STR_BANNED_WORDS = re.compile(
    r"no.short.term|no.vacation rental|no.str|no.rentals|no rental|"
    r"owner.occupied only|no airbnb|rental not permitted|no investor",
    re.IGNORECASE,
)

# Property type normalization
_HOME_TYPE_MAP = {
    "SINGLE_FAMILY": "single_family",
    "CONDO":         "condo",
    "TOWNHOUSE":     "townhouse",
    "MULTI_FAMILY":  "single_family",
    "MANUFACTURED":  "single_family",
}


# ── Geography helpers ─────────────────────────────────────────────────────────

def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in miles between two lat/lng points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _beach_distance(lat: float, lon: float, beach_coord: tuple | None) -> float | None:
    """Miles from property to nearest beach reference point."""
    if beach_coord is None:
        return None
    return round(_haversine_miles(lat, lon, beach_coord[0], beach_coord[1]), 2)


def _flood_zone_estimate(beach_dist: float | None) -> str:
    """
    Rough FEMA flood zone estimate from beach proximity.
    For precise zone: use FEMA NFHL API with lat/lng (adds latency; optional enhancement).
      VE  → oceanfront / dune line (≤ 0.2 mi)
      AE  → coastal moderate risk  (≤ 2.0 mi)
      X   → minimal risk           (> 2.0 mi or inland market)
    """
    if beach_dist is None:
        return "X"
    if beach_dist <= 0.2:
        return "VE"
    if beach_dist <= 2.0:
        return "AE"
    return "X"


# ── Caching ───────────────────────────────────────────────────────────────────

def _cache_path(key: str) -> str:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    h = hashlib.md5(key.encode()).hexdigest()[:12]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(_CACHE_DIR, f"{date_str}_{h}.json")


def _cache_get(key: str) -> dict | None:
    path = _cache_path(key)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def _cache_set(key: str, data: dict) -> None:
    with open(_cache_path(key), "w") as f:
        json.dump(data, f)


# ── Zillow API calls ──────────────────────────────────────────────────────────

class ZillowSource(ListingSource):
    """
    Fetches live STR-target listings from Zillow via RapidAPI.
    Requires RAPIDAPI_KEY in environment / .env file.
    """

    name = "zillow"
    _BASE = "https://zillow-com1.p.rapidapi.com"
    _HOST = "zillow-com1.p.rapidapi.com"

    # Search filters aligned with our hard-filter constants
    _MIN_PRICE = 550_000   # slightly below our MIN to catch near-threshold deals
    _MAX_PRICE = 1_250_000
    _MIN_BEDS  = 3
    _STATUS    = "forSale"

    def __init__(self, api_key: str | None = None):
        self._key = api_key or os.getenv("RAPIDAPI_KEY", "")
        if not self._key:
            raise RuntimeError(
                "RAPIDAPI_KEY not set. Add it to .env or pass api_key= directly.\n"
                "Get a key at: https://rapidapi.com/apimaker/api/zillow-com1"
            )
        self._headers = {
            "X-RapidAPI-Host": self._HOST,
            "X-RapidAPI-Key": self._key,
        }

    # ── Public interface ───────────────────────────────────────────────────────

    def fetch(self, market_ids: list[str] | None = None) -> list[PropertyListing]:
        """Search all configured markets and return PropertyListing objects."""
        configs = _MARKET_CONFIG
        if market_ids:
            configs = {k: v for k, v in configs.items() if k in market_ids}

        raw_results: dict[str, dict] = {}   # zpid → raw Zillow data + market_id

        for market_id, cfg in configs.items():
            for location in cfg["locations"]:
                hits = self._search(location)
                for hit in hits:
                    zpid = str(hit.get("zpid", ""))
                    if zpid and zpid not in raw_results:
                        raw_results[zpid] = {**hit, "_market_id": market_id, "_cfg": cfg}
                time.sleep(0.25)   # be polite to the API

        # Fetch full details only for properties that pass basic price/beds pre-filter
        listings: list[PropertyListing] = []
        for zpid, hit in raw_results.items():
            price = hit.get("price") or 0
            beds  = hit.get("bedrooms") or 0
            if price < self._MIN_PRICE or price > self._MAX_PRICE or beds < self._MIN_BEDS:
                continue

            detail = self._detail(zpid)
            listing = self._to_listing(zpid, hit, detail)
            if listing:
                listings.append(listing)
            time.sleep(0.25)

        return listings

    # ── API methods ────────────────────────────────────────────────────────────

    def _search(self, location: str) -> list[dict]:
        """Search Zillow for properties in a location. Returns list of raw hits."""
        cache_key = f"search:{location}:{self._MIN_PRICE}:{self._MAX_PRICE}:{self._MIN_BEDS}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        params = {
            "location":     location,
            "status_type":  self._STATUS,
            "home_type":    "Houses,Condos",
            "minPrice":     self._MIN_PRICE,
            "maxPrice":     self._MAX_PRICE,
            "bedsMin":      self._MIN_BEDS,
            "bathsMin":     2,
            "sort":         "Newest",
        }

        try:
            resp = requests.get(
                f"{self._BASE}/propertyExtendedSearch",
                headers=self._headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            props = data.get("props", [])
            _cache_set(cache_key, props)
            return props
        except Exception as e:
            print(f"  [Zillow] Search failed for '{location}': {e}")
            return []

    def _detail(self, zpid: str) -> dict:
        """Fetch full property detail. Returns empty dict on failure."""
        cache_key = f"detail:{zpid}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            resp = requests.get(
                f"{self._BASE}/property",
                headers=self._headers,
                params={"zpid": zpid},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data)
            return data
        except Exception as e:
            print(f"  [Zillow] Detail failed for zpid {zpid}: {e}")
            return {}

    # ── Field mapping ──────────────────────────────────────────────────────────

    def _to_listing(self, zpid: str, hit: dict, detail: dict) -> PropertyListing | None:
        """Convert raw Zillow data to a PropertyListing. Returns None if critical fields missing."""
        try:
            market_id = hit["_market_id"]
            cfg       = hit["_cfg"]

            # ── Address ───────────────────────────────────────────────────────
            address  = detail.get("address", {})
            street   = address.get("streetAddress") or hit.get("streetAddress", "Unknown")
            city     = address.get("city")          or hit.get("city", "")
            state    = address.get("state")         or hit.get("state", "")
            zip_code = address.get("zipcode")       or hit.get("zipcode", "")

            # ── Core specs ────────────────────────────────────────────────────
            price    = detail.get("price")    or hit.get("price")
            bedrooms = detail.get("bedrooms") or hit.get("bedrooms") or 0
            baths    = detail.get("bathrooms") or hit.get("bathrooms") or 0.0
            sqft     = detail.get("livingArea") or hit.get("livingArea") or 0
            yr_built = detail.get("yearBuilt") or hit.get("yearBuilt") or 0

            if not price or not bedrooms:
                return None

            # ── Property type ─────────────────────────────────────────────────
            home_type = detail.get("homeType") or hit.get("homeType", "SINGLE_FAMILY")
            prop_type = _HOME_TYPE_MAP.get(home_type, "single_family")

            # ── HOA ───────────────────────────────────────────────────────────
            reso = detail.get("resoFacts", {})
            hoa_fee_raw = reso.get("hoaFee") or detail.get("monthlyHoaFee")
            hoa_monthly = 0.0
            has_hoa     = False
            if hoa_fee_raw:
                try:
                    hoa_monthly = float(str(hoa_fee_raw).replace("$", "").replace(",", ""))
                    has_hoa = hoa_monthly > 0
                except (ValueError, TypeError):
                    pass

            # Try to detect STR permission from listing description
            description = detail.get("description", "") or ""
            if has_hoa and description:
                if _STR_OK_WORDS.search(description):
                    hoa_str_permitted: bool | None = True
                elif _STR_BANNED_WORDS.search(description):
                    hoa_str_permitted = False
                else:
                    hoa_str_permitted = None
            else:
                hoa_str_permitted = None   # unknown — scorer will penalise

            # ── Pool ──────────────────────────────────────────────────────────
            has_pool = bool(reso.get("hasPool")) or "pool" in description.lower()

            # ── Geography ─────────────────────────────────────────────────────
            lat = detail.get("latitude")  or hit.get("latitude")
            lon = detail.get("longitude") or hit.get("longitude")

            if lat and lon:
                beach_dist = _beach_distance(float(lat), float(lon), cfg["beach_coord"])
            else:
                beach_dist = None

            flood_zone = _flood_zone_estimate(beach_dist)

            # ── Market: use pool as fallback if lat/lon missing (use None for inland)
            if cfg["beach_coord"] is None:
                beach_dist = None   # inland market — no beach distance

            # ── Listing signals ────────────────────────────────────────────────
            dom = detail.get("daysOnZillow") or hit.get("daysOnZillow") or 0

            # Price history → original price + reduction
            price_history = detail.get("priceHistory") or []
            original_price = price
            price_reduction = 0.0
            if price_history:
                # Most recent "Listed for sale" event is the original price
                for event in reversed(price_history):
                    if "listed" in (event.get("event") or "").lower():
                        try:
                            original_price = float(event["price"])
                        except (KeyError, ValueError, TypeError):
                            pass
                        break
                price_reduction = max(0.0, original_price - price)

            # ── Zillow URL ────────────────────────────────────────────────────
            detail_url = detail.get("url") or hit.get("detailUrl") or ""
            if detail_url and not detail_url.startswith("http"):
                detail_url = f"https://www.zillow.com{detail_url}"

            return PropertyListing(
                listing_id=f"zillow_{zpid}",
                source="zillow",
                url=detail_url,
                address=street,
                city=city,
                state=state,
                zip_code=zip_code,
                market_id=market_id,
                price=float(price),
                bedrooms=int(bedrooms),
                bathrooms=float(baths),
                sqft=int(sqft),
                year_built=int(yr_built),
                property_type=prop_type,
                has_hoa=has_hoa,
                hoa_monthly=hoa_monthly,
                hoa_str_permitted=hoa_str_permitted,
                has_pool=has_pool,
                beach_distance_miles=beach_dist,
                airport_code=cfg["airport_code"],
                airport_drive_min=cfg["airport_drive_min"],
                flood_zone=flood_zone,
                days_on_market=int(dom),
                original_list_price=original_price,
                price_reduction=price_reduction,
            )

        except Exception as e:
            print(f"  [Zillow] Failed to parse zpid {zpid}: {e}")
            return None
