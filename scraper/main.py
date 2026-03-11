"""Main scraper orchestrator -- run by GitHub Action."""

import json
import os
from datetime import datetime, timezone

import requests

from scraper.config import (
    GOBLACKBEARS_BASE,
    AMERICA_EAST_BASE,
    HOCKEY_EAST_BASE,
    BDN_BASE,
    BDN_SPORTS_FEEDS,
    PRIORITY_SPORTS,
    SPORTS,
    USER_AGENT,
)
from scraper.schedules import fetch_schedules
from scraper.standings import fetch_standings
from scraper.box_scores import fetch_box_scores
from scraper.news import fetch_news
from scraper.rosters import fetch_rosters

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def run():
    """Run all scrapers and write JSON files."""
    now = datetime.now(timezone.utc)
    print("UMaine Sports Scraper")

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    # 1. Schedules
    print("1. Fetching schedules...")
    try:
        schedule_data = fetch_schedules(session, GOBLACKBEARS_BASE, SPORTS)
        _write_json("schedules.json", {
            "last_updated": now.isoformat(),
            "sports": schedule_data,
        })
    except Exception as e:
        print(f"  ERROR fetching schedules: {e}")
        schedule_data = {}

    # 2. Standings
    print("2. Fetching standings...")
    try:
        standings_data = fetch_standings(
            session, SPORTS, AMERICA_EAST_BASE, HOCKEY_EAST_BASE
        )
        _write_json("standings.json", {
            "last_updated": now.isoformat(),
            "conferences": standings_data,
        })
    except Exception as e:
        print(f"  ERROR fetching standings: {e}")

    # 3. Box scores (enrich sport configs with game_ids from schedule data)
    print("3. Fetching box scores...")
    try:
        sports_with_games = _merge_game_ids(SPORTS, schedule_data)
        box_data = fetch_box_scores(session, GOBLACKBEARS_BASE, sports_with_games)
        _write_json("box_scores.json", {
            "last_updated": now.isoformat(),
            "games": box_data,
        })
    except Exception as e:
        print(f"  ERROR fetching box scores: {e}")

    # 4. News
    print("4. Fetching news...")
    try:
        articles = fetch_news(
            session, GOBLACKBEARS_BASE, PRIORITY_SPORTS,
            bdn_base=BDN_BASE, bdn_feeds=BDN_SPORTS_FEEDS,
        )
        _write_json("news.json", {
            "last_updated": now.isoformat(),
            "articles": articles,
        })
    except Exception as e:
        print(f"  ERROR fetching news: {e}")

    # 5. Rosters
    print("5. Fetching rosters...")
    try:
        roster_data = fetch_rosters(session, GOBLACKBEARS_BASE, SPORTS)
        _write_json("rosters.json", {
            "last_updated": now.isoformat(),
            "sports": roster_data,
        })
    except Exception as e:
        print(f"  ERROR fetching rosters: {e}")

    print("Done.")


def _merge_game_ids(sports, schedule_data):
    """Create enriched sport configs with game_ids from schedule data.

    fetch_box_scores expects each sport dict to have a 'game_ids' list.
    fetch_schedules returns a dict mapping shortname -> schedule dict,
    where each schedule dict has a 'game_ids' key.  This function
    merges them together.

    Args:
        sports: List of sport config dicts from config.SPORTS.
        schedule_data: dict returned by fetch_schedules.

    Returns:
        list[dict]: Copy of sports configs with game_ids added.
    """
    enriched = []
    for sport in sports:
        shortname = sport.get("shortname", "")
        sched = schedule_data.get(shortname, {})
        game_ids = sched.get("game_ids", [])
        enriched.append({**sport, "game_ids": game_ids})
    return enriched


def _write_json(filename, data):
    """Write JSON file to data/ dir."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Wrote {path}")


if __name__ == "__main__":
    run()
