"""Parse GoBlackBears.com Sidearm roster HTML into structured player dicts.

The Sidearm CMS renders two (or more) templates of the same roster on a
single page -- a "card" view using ``<li class="sidearm-roster-player">``
elements, and a grid/table view.  Both carry ``data-player-id`` attributes.
We parse the card view (which has the richest markup) and deduplicate by
``data-player-id`` to avoid returning the same player twice.
"""

import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _extract_name_from_url(url):
    """Derive a clean player name from a ``data-player-url`` path.

    Example:
        "/sports/mens-ice-hockey/roster/lukas-peterson/12235"
        -> "Lukas Peterson"
    """
    if not url:
        return ""
    parts = url.strip("/").split("/")
    if len(parts) < 2:
        return ""
    slug = parts[-2]  # e.g. "lukas-peterson"
    return " ".join(word.capitalize() for word in slug.split("-"))


def _clean_text(el):
    """Get stripped text from a BeautifulSoup element, or empty string."""
    if el is None:
        return ""
    return el.get_text(strip=True)


def parse_roster(html):
    """Parse Sidearm roster HTML into a list of player dicts.

    Args:
        html: Raw HTML string from a sport's roster page.

    Returns:
        list[dict]: Each dict has keys player_id, name, number, position,
        height, weight, year, hometown, previous_school, headshot, url.
        Deduplicated by player_id.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "lxml")

    # Find all card-view player elements
    player_els = soup.find_all("li", class_="sidearm-roster-player")
    if not player_els:
        return []

    seen = set()
    players = []

    for li in player_els:
        player_id = li.get("data-player-id", "")
        if not player_id or player_id in seen:
            continue
        seen.add(player_id)

        player_url = li.get("data-player-url", "")

        # --- Name ---
        # The h3 > a inside sidearm-roster-player-name has the clean name
        name_div = li.find(class_="sidearm-roster-player-name")
        name = ""
        if name_div:
            link = name_div.find("a")
            if link:
                name = link.get_text(strip=True)
        # Fallback: derive from URL slug
        if not name:
            name = _extract_name_from_url(player_url)

        # --- Jersey number ---
        number_el = li.find(class_="sidearm-roster-player-jersey-number")
        number = _clean_text(number_el)

        # --- Position (use long form when available, fall back to short) ---
        pos_long = li.find(
            class_="sidearm-roster-player-position-long-short",
            attrs={"class": lambda c: c and "hide-on-small-down" in c},
        )
        if pos_long:
            position = _clean_text(pos_long)
        else:
            pos_el = li.find(class_="sidearm-roster-player-position-long-short")
            position = _clean_text(pos_el)

        # --- Height / Weight ---
        height = _clean_text(li.find(class_="sidearm-roster-player-height"))
        weight = _clean_text(li.find(class_="sidearm-roster-player-weight"))

        # --- Academic year (prefer the desktop-visible one) ---
        year_els = li.find_all(class_="sidearm-roster-player-academic-year")
        year = ""
        for yel in year_els:
            # The desktop version is inside the hide-on-medium-down div
            parent_other = yel.find_parent(class_="sidearm-roster-player-other")
            if parent_other and "hide-on-medium-down" not in (
                " ".join(parent_other.get("class", []))
            ):
                year = _clean_text(yel)
                break
        if not year and year_els:
            year = _clean_text(year_els[0])

        # --- Hometown ---
        hometown_els = li.find_all(class_="sidearm-roster-player-hometown")
        hometown = ""
        for hel in hometown_els:
            text = _clean_text(hel)
            if text:
                hometown = text
                break

        # --- Previous school ---
        prev_els = li.find_all(class_="sidearm-roster-player-previous-school")
        previous_school = ""
        for pel in prev_els:
            text = _clean_text(pel)
            if text:
                previous_school = text
                break

        # --- Headshot ---
        headshot = ""
        img = li.find("img", attrs={"data-src": True})
        if img:
            headshot = img["data-src"]

        players.append({
            "player_id": player_id,
            "name": name,
            "number": number,
            "position": position,
            "height": height,
            "weight": weight,
            "year": year,
            "hometown": hometown,
            "previous_school": previous_school,
            "headshot": headshot,
            "url": player_url,
        })

    return players


def fetch_rosters(session, base_url, sports):
    """Fetch and parse rosters for a list of sports.

    Args:
        session: requests.Session with appropriate headers.
        base_url: Base URL (e.g. "https://goblackbears.com").
        sports: List of sport config dicts (must have 'slug' key).

    Returns:
        dict mapping sport shortname to list of player dicts.
    """
    results = {}

    for sport in sports:
        slug = sport["slug"]
        shortname = sport.get("shortname", slug)

        roster_url = f"{base_url}/sports/{slug}/roster"
        logger.info("Fetching roster: %s", roster_url)

        try:
            resp = session.get(roster_url)
            resp.raise_for_status()
        except Exception:
            logger.exception("Failed to fetch roster for %s", shortname)
            continue

        players = parse_roster(resp.text)
        results[shortname] = players
        logger.info("Parsed %d players for %s", len(players), shortname)

    return results
