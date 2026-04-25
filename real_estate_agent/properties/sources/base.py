"""
Abstract base for listing data sources.
Each concrete source implements fetch() and returns PropertyListing objects.

To add a real source (e.g. Zillow RapidAPI):
  1. Subclass ListingSource
  2. Implement fetch() to call the API and parse responses
  3. Register in ranker.py's build_pipeline()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from real_estate_agent.properties.models import PropertyListing


class ListingSource(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, market_ids: list[str] | None = None) -> list[PropertyListing]:
        """
        Fetch listings. If market_ids is provided, filter to those markets only.
        Returns raw (unenriched) PropertyListing objects.
        """
        ...
