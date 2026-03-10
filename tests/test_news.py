"""Tests for RSS news scraper."""

import os
import pytest
from scraper.news import parse_rss


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def rss_xml():
    path = os.path.join(FIXTURE_DIR, "rss_mhockey.xml")
    with open(path) as f:
        return f.read()


@pytest.fixture
def articles(rss_xml):
    return parse_rss(rss_xml)


class TestParseRss:
    def test_returns_list(self, articles):
        assert isinstance(articles, list)

    def test_has_articles(self, articles):
        assert len(articles) > 0

    def test_article_has_required_fields(self, articles):
        article = articles[0]
        for field in ["title", "url", "summary", "image", "published", "sport"]:
            assert field in article, f"Missing field: {field}"

    def test_title_not_empty(self, articles):
        for article in articles:
            assert article["title"].strip() != "", f"Empty title in {article}"

    def test_url_is_full(self, articles):
        for article in articles:
            assert article["url"].startswith("http"), (
                f"URL does not start with http: {article['url']}"
            )

    def test_sport_category(self, articles):
        for article in articles:
            assert "sport" in article
            assert article["sport"] != "", f"Empty sport in {article}"

    def test_empty_input(self):
        result = parse_rss("")
        assert result == []

    def test_summary_has_no_img_tags(self, articles):
        for article in articles:
            assert "<img" not in article["summary"], (
                f"Summary still contains <img> tag: {article['summary']}"
            )

    def test_image_is_url(self, articles):
        for article in articles:
            if article["image"]:
                assert article["image"].startswith("http"), (
                    f"Image is not a URL: {article['image']}"
                )

    def test_published_is_string(self, articles):
        for article in articles:
            assert isinstance(article["published"], str)
            assert len(article["published"]) > 0
