"""Scrape news articles from GoBlackBears.com and BDN RSS feeds.

The RSS feeds at goblackbears.com/rss provide news articles with
media content, sport categories, and publication dates.  BDN sports
category feeds provide professional coverage filtered to UMaine content.
This module parses the XML into structured article dicts and provides
fetch helpers that retrieve feeds from both sources.
"""

import re
import logging

import feedparser

logger = logging.getLogger(__name__)

# Keywords (lowercase) that indicate UMaine-related BDN articles
_UMAINE_KEYWORDS = re.compile(
    r"umaine|black bear|university of maine|america east|hockey east"
    r"|goblackbears|alfond|orono",
    re.IGNORECASE,
)

# Regex to strip <img ...> tags (and self-closing variants) from summaries
_IMG_TAG_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)

# Regex to strip all HTML tags from summaries
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_summary(raw):
    """Remove <img> tags and clean up the summary text.

    The RSS feed summaries typically contain an <img> tag followed by
    <br /> tags and then the actual summary text.
    """
    if not raw:
        return ""
    # Remove <img> tags
    text = _IMG_TAG_RE.sub("", raw)
    # Strip remaining HTML tags
    text = _HTML_TAG_RE.sub("", text)
    return text.strip()


def _extract_image(entry):
    """Extract the best image URL from a feed entry.

    Prefers media_content over media_thumbnail.
    """
    # Try media:content first
    media_content = entry.get("media_content", [])
    if media_content and media_content[0].get("url"):
        return media_content[0]["url"]

    # Fall back to media:thumbnail
    media_thumbnail = entry.get("media_thumbnail", [])
    if media_thumbnail and media_thumbnail[0].get("url"):
        return media_thumbnail[0]["url"]

    return ""


def _extract_sport(entry):
    """Extract the sport category from a feed entry's tags."""
    tags = entry.get("tags", [])
    if tags and tags[0].get("term"):
        return tags[0]["term"]
    return ""


def parse_rss(xml, source="goblackbears"):
    """Parse RSS XML into a list of article dicts.

    Args:
        xml: Raw XML string from an RSS feed.
        source: Source identifier ("goblackbears" or "bdn").

    Returns:
        list[dict]: Each dict has keys: title, url, summary, image,
            published, sport, source.
    """
    if not xml or not xml.strip():
        return []

    feed = feedparser.parse(xml)
    articles = []

    for entry in feed.entries:
        article = {
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": _clean_summary(entry.get("summary", "")),
            "image": _extract_image(entry),
            "published": entry.get("published", ""),
            "sport": _extract_sport(entry),
            "source": source,
        }
        if source == "bdn":
            article["author"] = entry.get("author", "")
        articles.append(article)

    return articles


def _is_umaine_article(article):
    """Check if a BDN article is UMaine-related by searching title,
    summary, and sport/category fields."""
    text = " ".join([
        article.get("title", ""),
        article.get("summary", ""),
        article.get("sport", ""),
    ])
    return bool(_UMAINE_KEYWORDS.search(text))


def parse_bdn_rss(xml):
    """Parse BDN RSS XML, keeping only UMaine-related articles.

    Args:
        xml: Raw XML string from a BDN category feed.

    Returns:
        list[dict]: UMaine-related article dicts with source="bdn".
    """
    all_articles = parse_rss(xml, source="bdn")
    return [a for a in all_articles if _is_umaine_article(a)]


def fetch_news(session, base_url, shortnames, bdn_base=None, bdn_feeds=None):
    """Fetch news articles from GoBlackBears and BDN RSS feeds.

    Retrieves the general feed plus one feed per sport shortname,
    then optionally fetches BDN category feeds and filters for
    UMaine-related content.  Deduplicates articles by URL.

    Args:
        session: requests.Session with appropriate headers.
        base_url: Base URL (e.g. "https://goblackbears.com").
        shortnames: List of sport shortname strings (e.g. ["mhockey", "wbball"]).
        bdn_base: BDN base URL (e.g. "https://www.bangordailynews.com").
        bdn_feeds: List of BDN feed paths (e.g. ["/category/sports/feed/"]).

    Returns:
        list[dict]: Deduplicated list of article dicts, newest first.
    """
    seen_urls = set()
    articles = []

    def _add(article):
        if article["url"] and article["url"] not in seen_urls:
            seen_urls.add(article["url"])
            articles.append(article)

    # --- GoBlackBears feeds ---
    general_url = f"{base_url}/rss"
    logger.info("Fetching general RSS feed: %s", general_url)
    try:
        resp = session.get(general_url)
        resp.raise_for_status()
        for a in parse_rss(resp.text, source="goblackbears"):
            _add(a)
    except Exception:
        logger.exception("Failed to fetch general RSS feed")

    for shortname in shortnames:
        url = f"{base_url}/rss?path={shortname}"
        logger.info("Fetching RSS feed: %s", url)
        try:
            resp = session.get(url)
            resp.raise_for_status()
            for a in parse_rss(resp.text, source="goblackbears"):
                _add(a)
        except Exception:
            logger.exception("Failed to fetch RSS feed for %s", shortname)

    # --- BDN feeds ---
    if bdn_base and bdn_feeds:
        for feed_path in bdn_feeds:
            url = f"{bdn_base}{feed_path}"
            logger.info("Fetching BDN feed: %s", url)
            try:
                resp = session.get(url)
                resp.raise_for_status()
                for a in parse_bdn_rss(resp.text):
                    _add(a)
            except Exception:
                logger.exception("Failed to fetch BDN feed: %s", url)

    return articles
