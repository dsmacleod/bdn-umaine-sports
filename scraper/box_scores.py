"""Parse box score data from GoBlackBears.com responsive-schedule endpoint.

The responsive-schedule.ashx endpoint returns JSON containing box score
details for a single game, including teams, scores by period, statistical
leaders, location, attendance, and an associated news story recap.

This module cleans the raw JSON (stripping HTML from leader names and
story teasers, trimming zero-score overtime periods) and provides a
fetch helper to retrieve box scores for recent games across sports.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Regex to strip HTML tags
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text):
    """Remove all HTML tags from a string."""
    if not text:
        return ""
    return _HTML_TAG_RE.sub("", text).strip()


def _parse_periods(score_by_periods):
    """Filter score_by_periods to meaningful periods.

    The endpoint always returns 5 entries (3 regulation + 2 OT).
    We keep all 3 regulation periods plus any OT periods with
    non-zero scores.

    Args:
        score_by_periods: list of {"period": "1", "score": "0"} dicts.

    Returns:
        list of period dicts with only meaningful entries.
    """
    if not score_by_periods:
        return []

    result = []
    for entry in score_by_periods:
        period_num = int(entry.get("period", 0))
        score = entry.get("score", "0")

        # Always include regulation periods (1-3)
        if period_num <= 3:
            result.append({"period": entry["period"], "score": score})
        # Only include OT periods with non-zero scores
        elif score != "0":
            result.append({"period": entry["period"], "score": score})

    return result


def _parse_leaders(leaders):
    """Parse leaders list, stripping HTML from names.

    Args:
        leaders: list of {"name": "...", "stat": "...", "value": "..."} dicts.

    Returns:
        list of cleaned leader dicts.
    """
    if not leaders:
        return []

    result = []
    for leader in leaders:
        result.append({
            "name": _strip_html(leader.get("name", "")),
            "stat": leader.get("stat", ""),
            "value": leader.get("value", ""),
        })
    return result


def _parse_team(team_data):
    """Parse a single team's box score data.

    Args:
        team_data: dict with name, score, score_by_periods, leaders, etc.

    Returns:
        Cleaned team dict.
    """
    if not team_data:
        return {"name": "", "score": "", "id": "", "record": "",
                "periods": [], "leaders": []}

    return {
        "name": team_data.get("name", ""),
        "score": team_data.get("score", ""),
        "id": team_data.get("id", ""),
        "record": team_data.get("record", ""),
        "periods": _parse_periods(team_data.get("score_by_periods", [])),
        "leaders": _parse_leaders(team_data.get("leaders", [])),
    }


def _parse_recap(story_data):
    """Parse the story/recap section, stripping HTML from teaser.

    Args:
        story_data: dict with headline, teaser, date, image, url.

    Returns:
        Cleaned recap dict.
    """
    if not story_data:
        return {"headline": "", "teaser": "", "date": "", "image": "", "url": ""}

    return {
        "headline": story_data.get("headline", ""),
        "teaser": _strip_html(story_data.get("teaser", "")),
        "date": story_data.get("date", ""),
        "image": story_data.get("image", ""),
        "url": story_data.get("url", ""),
    }


def parse_box_score(data):
    """Clean and structure raw box score JSON.

    Args:
        data: dict from responsive-schedule.ashx JSON response.

    Returns:
        dict with keys: home, away, location, attendance, recap,
        result_status, url.
    """
    if not data:
        return {
            "home": _parse_team(None),
            "away": _parse_team(None),
            "location": "",
            "attendance": "",
            "recap": _parse_recap(None),
            "result_status": "",
            "url": "",
        }

    boxscore = data.get("boxscore", {})

    return {
        "home": _parse_team(boxscore.get("home")),
        "away": _parse_team(boxscore.get("away")),
        "location": boxscore.get("location", ""),
        "attendance": boxscore.get("attendance", ""),
        "recap": _parse_recap(data.get("story")),
        "result_status": data.get("result_status", ""),
        "url": boxscore.get("url", ""),
    }


def fetch_box_scores(session, base_url, sports, max_per_sport=5):
    """Fetch recent game box scores for a list of sports.

    For each sport, uses previously discovered game_ids from the schedule
    scraper to fetch individual box scores from the responsive-schedule
    endpoint.

    Args:
        session: requests.Session with appropriate headers.
        base_url: Base URL (e.g. "https://goblackbears.com").
        sports: List of sport config dicts (must have 'sport_id' and
            'shortname' keys; 'game_ids' list is expected from schedule data).
        max_per_sport: Maximum number of box scores to fetch per sport.

    Returns:
        dict mapping sport shortname to list of parsed box score dicts.
    """
    results = {}

    for sport in sports:
        sport_id = sport.get("sport_id")
        shortname = sport.get("shortname", "")
        game_ids = sport.get("game_ids", [])

        if not sport_id or not game_ids:
            logger.info("Skipping %s: no sport_id or game_ids", shortname)
            continue

        box_scores = []
        for game_id in game_ids[:max_per_sport]:
            url = (f"{base_url}/services/responsive-schedule.ashx"
                   f"?game_id={game_id}&sport_id={sport_id}")
            logger.info("Fetching box score: %s", url)

            try:
                resp = session.get(url)
                resp.raise_for_status()
                raw = resp.json()
            except Exception:
                logger.exception("Failed to fetch box score game_id=%s", game_id)
                continue

            parsed = parse_box_score(raw)
            parsed["game_id"] = game_id
            parsed["sport"] = shortname
            box_scores.append(parsed)

        if box_scores:
            results[shortname] = box_scores

    return results
