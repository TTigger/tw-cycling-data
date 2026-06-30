# -*- coding: utf-8 -*-
"""HTTP access layer for the tw-cycling-data public v1 API. The fetch callable
is injectable so tests never hit the network."""
import os

DEFAULT_BASE = "https://tw-cycling-data.vercel.app/data/v1"


def _httpx_fetch(url):
    import httpx
    r = httpx.get(url, timeout=15.0, follow_redirects=True)
    r.raise_for_status()
    return r.json()


class ApiClient:
    def __init__(self, base_url=None, fetch=None):
        self.base = (base_url or os.environ.get("TWCD_API_BASE") or DEFAULT_BASE).rstrip("/")
        self._fetch = fetch or _httpx_fetch

    def _get(self, path):
        return self._fetch(f"{self.base}/{path}")

    def manifest(self):
        return self._get("manifest.json")

    def athletes_index(self):
        return self._get("athletes.json")

    def athlete(self, athlete_id):
        return self._get(f"athlete/{athlete_id}.json")

    def races_index(self):
        return self._get("races.json")

    def race(self, file_stem):
        return self._get(f"race/{file_stem}.json")

    def team(self, team_id):
        return self._get(f"team/{team_id}.json")
