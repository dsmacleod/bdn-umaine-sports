"""Parse GoBlackBears.com schedule_txt plaintext format.

The schedule_txt.ashx endpoint returns fixed-width plaintext with team
records followed by a columnar game listing.  This module parses that
format into structured dicts and provides helpers for discovering
schedule IDs from HTML schedule pages.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Record labels we extract from the header block
_RECORD_LABELS = {"overall", "conference", "streak", "home", "away", "neutral"}


def _parse_records(lines):
    """Extract W-L-T records and streak from the header block.

    Lines look like:
        Overall    18-13-3  .574
        Conference 12-11-1  .521
        Streak     L1
    """
    record = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            label = parts[0].lower()
            if label in _RECORD_LABELS:
                record[label] = parts[1]
    return record


def _find_column_positions(header_line):
    """Determine column start positions from the header line.

    Returns a dict mapping column name to its character offset.
    Expected columns: Date, Time, At, Opponent, Location, Tournament, Result
    """
    columns = ["Date", "Time", "At", "Opponent", "Location", "Tournament", "Result"]
    positions = {}
    for col in columns:
        idx = header_line.find(col)
        if idx >= 0:
            positions[col] = idx
    return positions


def _parse_game_line(line, positions):
    """Parse a single game row using column positions.

    Returns a dict with date, time, home_away, opponent, location,
    tournament, and result fields.
    """
    def _extract(col, next_col=None):
        start = positions.get(col)
        if start is None:
            return ""
        end = positions.get(next_col) if next_col else None
        if end is not None:
            return line[start:end].strip()
        return line[start:].strip()

    # Ordered column pairs for extraction
    col_order = ["Date", "Time", "At", "Opponent", "Location", "Tournament", "Result"]

    fields = {}
    for i, col in enumerate(col_order):
        next_col = col_order[i + 1] if i + 1 < len(col_order) else None
        fields[col] = _extract(col, next_col)

    return {
        "date": fields.get("Date", ""),
        "time": fields.get("Time", ""),
        "home_away": fields.get("At", ""),
        "opponent": fields.get("Opponent", ""),
        "location": fields.get("Location", ""),
        "tournament": fields.get("Tournament", ""),
        "result": fields.get("Result", ""),
    }


def parse_schedule_txt(text):
    """Parse schedule_txt plaintext into a structured dict.

    Args:
        text: Raw plaintext from schedule_txt.ashx endpoint.

    Returns:
        dict with keys:
            - record: dict with overall, conference, streak, home, away, neutral
            - games: list of game dicts
    """
    if not text or not text.strip():
        return {"record": {}, "games": []}

    lines = text.splitlines()

    # Find the header line that starts with "Date"
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Date"):
            header_idx = i
            break

    if header_idx is None:
        return {"record": {}, "games": []}

    # Parse records from lines before the header
    record = _parse_records(lines[:header_idx])

    # Get column positions from header
    positions = _find_column_positions(lines[header_idx])

    # Parse game lines (everything after header)
    games = []
    for line in lines[header_idx + 1:]:
        if not line.strip():
            continue
        game = _parse_game_line(line, positions)
        # Skip lines that don't look like game rows
        if game["date"] and game["opponent"]:
            games.append(game)

    return {"record": record, "games": games}


def discover_schedule_id(html):
    """Extract schedule_txt ID from a schedule page's HTML.

    Looks for links/references to schedule_txt.ashx?schedule=NNNN.

    Args:
        html: Raw HTML string from a sport's schedule page.

    Returns:
        str: The schedule ID, or None if not found.
    """
    match = re.search(r"schedule_txt\.ashx\?schedule=(\d+)", html)
    if match:
        return match.group(1)
    return None


def discover_game_ids(html):
    """Extract game IDs from schedule page HTML.

    Sidearm Sports schedule pages include data-game-id attributes
    on game row elements.

    Args:
        html: Raw HTML string from a sport's schedule page.

    Returns:
        list[str]: List of game ID strings.
    """
    return re.findall(r'data-game-id=["\'](\d+)["\']', html)


def fetch_schedules(session, base_url, sports):
    """Fetch and parse schedules for a list of sports.

    For each sport configuration dict:
    1. Fetch the sport's schedule page HTML
    2. Discover the schedule_txt ID from the HTML
    3. Fetch the plaintext schedule
    4. Parse it into structured data

    Args:
        session: requests.Session with appropriate headers.
        base_url: Base URL (e.g. "https://goblackbears.com").
        sports: List of sport config dicts (must have 'slug' key).

    Returns:
        dict mapping sport shortname to parsed schedule dict.
    """
    results = {}

    for sport in sports:
        slug = sport["slug"]
        shortname = sport.get("shortname", slug)

        schedule_url = f"{base_url}/sports/{slug}/schedule"
        logger.info("Fetching schedule page: %s", schedule_url)

        try:
            resp = session.get(schedule_url)
            resp.raise_for_status()
        except Exception:
            logger.exception("Failed to fetch schedule page for %s", shortname)
            continue

        schedule_id = discover_schedule_id(resp.text)
        if not schedule_id:
            logger.warning("No schedule_txt ID found for %s", shortname)
            continue

        txt_url = f"{base_url}/services/schedule_txt.ashx?schedule={schedule_id}"
        logger.info("Fetching schedule_txt: %s", txt_url)

        try:
            txt_resp = session.get(txt_url)
            txt_resp.raise_for_status()
        except Exception:
            logger.exception("Failed to fetch schedule_txt for %s", shortname)
            continue

        parsed = parse_schedule_txt(txt_resp.text)
        parsed["schedule_id"] = schedule_id
        parsed["game_ids"] = discover_game_ids(resp.text)
        results[shortname] = parsed

    return results
