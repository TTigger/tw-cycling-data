# -*- coding: utf-8 -*-
"""FastMCP server exposing the tw-cycling-data public API as MCP tools.
Reads the live /data/v1 endpoints over HTTP. Tool logic lives in *_impl
functions (client injected) so it is unit-testable without a server."""
import asyncio

from mcp.server.fastmcp import FastMCP

from . import query as _query_module
from .client import ApiClient

mcp = FastMCP("tw-cycling-data")
_client = ApiClient()


# ---- impls (client injected; unit-testable) ----

def dataset_overview_impl(client):
    return client.manifest()


def search_athletes_impl(client, q, limit):
    return _query_module.match_athletes(client.athletes_index(), q, limit)


def get_athlete_impl(client, athlete_id):
    return client.athlete(athlete_id)


def list_races_impl(client, year, race_type, q, limit):
    return _query_module.filter_races(client.races_index(), year, race_type, q, limit)


def get_race_impl(client, race_key, year=None):
    idx = client.races_index()
    # A direct file-stem match (the value list_races returns in `file`) wins.
    if any(r.get("file") == race_key for r in idx):
        return client.race(race_key)
    matches = [r for r in idx if r.get("rk") == race_key]
    if year is not None:
        matches = [r for r in matches if r.get("y") == year]
    if matches:
        # A race_key can span multiple years; default to the latest edition.
        chosen = max(matches, key=lambda r: (r.get("y") or 0))
        return client.race(chosen["file"])
    return client.race(race_key)  # fallback: treat the input as a file stem


def get_team_impl(client, team_id):
    return client.team(team_id)


def race_benchmark_impl(client, race_key, finish_time, age_band, gender):
    seconds = _query_module.hms_to_seconds(finish_time)
    if seconds is None:
        return {"error": f"could not parse finish_time '{finish_time}' (use HH:MM:SS / MM:SS / seconds)"}
    return _query_module.benchmark_lookup(client.benchmarks(), race_key, seconds, age_band, gender)


# ---- MCP tools ----

@mcp.tool()
def dataset_overview() -> dict:
    """Dataset size, year range, source count, and license (from manifest.json)."""
    return dataset_overview_impl(_client)


@mcp.tool()
def search_athletes(query: str, limit: int = 20) -> list:
    """Search athletes by visible (masked) name or athlete_id prefix. PDPA: masked names only."""
    return search_athletes_impl(_client, query, limit)


@mcp.tool()
def get_athlete(athlete_id: str) -> dict:
    """One athlete's de-identified result history."""
    return get_athlete_impl(_client, athlete_id)


@mcp.tool()
def list_races(year: int = None, race_type: str = None, query: str = None, limit: int = 50) -> list:
    """List races, optionally filtered by year, series, or name substring."""
    return list_races_impl(_client, year, race_type, query, limit)


@mcp.tool()
def get_race(race_key: str, year: int = None) -> dict:
    """One race leaderboard (re-ranked by category + finish time). A race_key can
    span multiple years; without `year` the latest edition is returned. For an
    exact edition, pass `year`, or pass the `file` value from list_races as race_key."""
    return get_race_impl(_client, race_key, year)


@mcp.tool()
def get_team(team_id: str) -> dict:
    """One team's roster and record."""
    return get_team_impl(_client, team_id)


@mcp.tool()
def race_benchmark(race_key: str, finish_time: str, age_band: str = None, gender: str = None) -> dict:
    """Percentile a finish time beats within a race's age/gender/category cohort.
    finish_time accepts HH:MM:SS / MM:SS / seconds; age_band like '40-49'; gender 'M'/'F'.
    PDPA: aggregate only."""
    return race_benchmark_impl(_client, race_key, finish_time, age_band, gender)


def tool_names() -> list[str]:
    """Return registered tool names. Handles both async list_tools() and internal _tool_manager."""
    try:
        tools = asyncio.run(mcp.list_tools())
        return [t.name for t in tools]
    except Exception:
        return list(mcp._tool_manager._tools.keys())


def main():
    mcp.run()


if __name__ == "__main__":
    main()
