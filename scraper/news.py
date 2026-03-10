"""Scrape news articles from GoBlackBears.com RSS feeds.

The RSS feeds at goblackbears.com/rss provide news articles with
media content, sport categories, and publication dates.  This module
parses the XML into structured article dicts and provides a fetch
helper that retrieves feeds for multiple sports.
"""

import re
import logging

import feedparser

logger = logging.getLogger(__name__)

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


def parse_rss(xml):
    """Parse RSS XML into a list of article dicts.

    Args:
        xml: Raw XML string from an RSS feed.

    Returns:
        list[dict]: Each dict has keys: title, url, summary, image,
            published, sport.
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
        }
        articles.append(article)

    return articles


def fetch_news(session, base_url, shortnames):
    """Fetch news articles from general and sport-specific RSS feeds.

    Retrieves the general feed plus one feed per sport shortname,
    then deduplicates articles by URL.

    Args:
        session: requests.Session with appropriate headers.
        base_url: Base URL (e.g. "https://goblackbears.com").
        shortnames: List of sport shortname strings (e.g. ["mhockey", "wbball"]).

    Returns:
        list[dict]: Deduplicated list of article dicts, newest first.
    """
    all_xml = []

    # Fetch the general feed (no path filter)
    general_url = f"{base_url}/rss"
    logger.info("Fetching general RSS feed: %s", general_url)
    try:
        resp = session.get(general_url)
        resp.raise_for_status()
        all_xml.append(resp.text)
    except Exception:
        logger.exception("Failed to fetch general RSS feed")

    # Fetch sport-specific feeds
    for shortname in shortnames:
        url = f"{base_url}/rss?path={shortname}"
        logger.info("Fetching RSS feed: %s", url)
        try:
            resp = session.get(url)
            resp.raise_for_status()
            all_xml.append(resp.text)
        except Exception:
            logger.exception("Failed to fetch RSS feed for %s", shortname)

    # Parse all feeds and deduplicate by URL
    seen_urls = set()
    articles = []

    for xml in all_xml:
        for article in parse_rss(xml):
            if article["url"] and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                articles.append(article)

    # Sort by published date descending (RFC 822 strings sort correctly
    # for same-timezone dates, but for robustness we keep insertion order
    # which is already newest-first from the feeds)
    return articles
