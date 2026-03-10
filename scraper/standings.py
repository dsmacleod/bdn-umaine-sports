"""Parse conference standings from America East (JSON) and Hockey East (HTML).

America East provides a JSON API at:
    https://americaeast.com/services/standings.ashx?path=<sport>

Hockey East publishes an HTML standings table at:
    https://www.hockeyeastonline.com/<gender>/standings/index.php
"""

import re
import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────


def _strip_html(text):
    """Remove HTML tags from *text*, returning plain text."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def _clean_school_name(raw):
    """Strip HTML tags and clinch markers (e.g. ' -x', ' -y', ' -z') from a school name."""
    name = _strip_html(raw)
    # Remove clinch suffixes like " -x", " -y", " -z"
    name = re.sub(r"\s+-[a-z]$", "", name)
    return name.strip()


# ── America East (JSON) ──────────────────────────────────────────────


def parse_america_east(data):
    """Parse America East standings JSON into a normalised dict.

    Args:
        data: Decoded JSON dict from the standings.ashx endpoint.

    Returns:
        dict with keys:
            - title (str): Display title from the response.
            - teams (list[dict]): Each team dict has school, conference,
              overall, pct (conference pct), streak, is_umaine.
    """
    standings = data.get("Standings", {})
    schedules = standings.get("Schedules", {})
    details = data.get("Details", {})

    if not schedules:
        return {"title": details.get("standings_display_title", ""), "teams": []}

    teams = []
    for _schedule_id, entry in schedules.items():
        school = _clean_school_name(entry.get("School", ""))
        team = {
            "school": school,
            "conference": entry.get("Conference", ""),
            "conference_pct": entry.get("CPercent", ""),
            "overall": entry.get("Overall", ""),
            "pct": entry.get("CPercent", ""),
            "streak": entry.get("Streak", ""),
            "is_umaine": school == "Maine",
        }
        teams.append(team)

    # Sort by conference pct descending (matching the sort_string from the API)
    teams.sort(key=lambda t: float(t["pct"] or "0"), reverse=True)

    return {
        "title": details.get("standings_display_title", ""),
        "notes": details.get("standings_notes", ""),
        "teams": teams,
    }


# ── Hockey East (HTML) ───────────────────────────────────────────────

# Column mapping for the data rows. Each data <tr> has cells in this order:
# rank, school, conf_gp, conf_pts, conf_w, conf_l, conf_t,
# conf_ow, conf_ol, conf_sw, conf_gf, conf_ga,
# (blank separator), overall_gp, overall_w, overall_l, overall_t, overall_gf, overall_ga

_CONF_FIELDS = ["gp", "pts", "w", "l", "t", "ow", "ol", "sw", "gf", "ga"]
_OVERALL_FIELDS = ["gp", "w", "l", "t", "gf", "ga"]


def parse_hockey_east(html):
    """Parse Hockey East standings HTML into a normalised dict.

    Args:
        html: Raw HTML string from the standings page.

    Returns:
        dict with key:
            - teams (list[dict]): Each team dict has school, rank,
              conference (dict), overall (dict), is_umaine.
    """
    if not html or not html.strip():
        return {"teams": []}

    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="data")
    if not table:
        return {"teams": []}

    rows = table.find_all("tr")
    # Skip the 2 header rows (th rows)
    data_rows = [r for r in rows if r.find("td")]

    teams = []
    for row in data_rows:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) < 19:
            continue

        # cells[0] = rank (may be empty for tied teams)
        rank_str = cells[0]
        rank = int(rank_str) if rank_str.isdigit() else None

        school = cells[1]

        # Conference stats: cells[2..11] (10 fields)
        conf = {}
        for i, field in enumerate(_CONF_FIELDS):
            val = cells[2 + i]
            conf[field] = int(val) if val.isdigit() else 0

        # cells[12] is the blank separator column
        # Overall stats: cells[13..18] (6 fields)
        overall = {}
        for i, field in enumerate(_OVERALL_FIELDS):
            val = cells[13 + i]
            overall[field] = int(val) if val.isdigit() else 0

        teams.append({
            "school": school,
            "rank": rank,
            "conference": conf,
            "overall": overall,
            "is_umaine": school == "Maine",
        })

    return {"teams": teams}


# ── Fetch helpers ─────────────────────────────────────────────────────


def fetch_standings(session, sports, ae_base, he_base):
    """Fetch and parse standings for all configured sports.

    Args:
        session: requests.Session with appropriate headers.
        sports: List of sport config dicts from config.SPORTS.
        ae_base: America East base URL.
        he_base: Hockey East base URL.

    Returns:
        dict mapping sport shortname to parsed standings dict.
    """
    results = {}

    for sport in sports:
        shortname = sport.get("shortname", "")
        conference = sport.get("conference", "")

        if conference == "america_east" and sport.get("ae_path"):
            ae_path = sport["ae_path"]
            url = f"{ae_base}/services/standings.ashx?path={ae_path}"
            logger.info("Fetching AE standings: %s", url)
            try:
                resp = session.get(url)
                resp.raise_for_status()
                data = resp.json()
                results[shortname] = parse_america_east(data)
            except Exception:
                logger.exception("Failed to fetch AE standings for %s", shortname)

        elif conference == "hockey_east":
            gender = "women" if shortname == "whockey" else "men"
            url = f"{he_base}/{gender}/standings/index.php"
            logger.info("Fetching HE standings: %s", url)
            try:
                resp = session.get(url)
                resp.raise_for_status()
                results[shortname] = parse_hockey_east(resp.text)
            except Exception:
                logger.exception("Failed to fetch HE standings for %s", shortname)

    return results
