"""Tests for RSS news scraper."""

import os
import pytest
from scraper.news import parse_rss, parse_bdn_rss, _is_umaine_article


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def rss_xml():
    path = os.path.join(FIXTURE_DIR, "rss_mhockey.xml")
    with open(path) as f:
        return f.read()


@pytest.fixture
def bdn_xml():
    path = os.path.join(FIXTURE_DIR, "bdn_sports_feed.xml")
    with open(path) as f:
        return f.read()


@pytest.fixture
def articles(rss_xml):
    return parse_rss(rss_xml)


@pytest.fixture
def bdn_articles(bdn_xml):
    return parse_bdn_rss(bdn_xml)


class TestParseRss:
    def test_returns_list(self, articles):
        assert isinstance(articles, list)

    def test_has_articles(self, articles):
        assert len(articles) > 0

    def test_article_has_required_fields(self, articles):
        article = articles[0]
        for field in ["title", "url", "summary", "image", "published", "sport", "source"]:
            assert field in article, f"Missing field: {field}"

    def test_source_is_goblackbears(self, articles):
        for article in articles:
            assert article["source"] == "goblackbears"

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


class TestParseBdnRss:
    def test_returns_list(self, bdn_articles):
        assert isinstance(bdn_articles, list)

    def test_filters_to_umaine_only(self, bdn_articles):
        for article in bdn_articles:
            text = f"{article['title']} {article['summary']} {article['sport']}"
            assert any(
                kw in text.lower()
                for kw in ["umaine", "black bear", "university of maine",
                           "america east", "hockey east", "alfond", "orono"]
            ), f"Non-UMaine article slipped through: {article['title']}"

    def test_source_is_bdn(self, bdn_articles):
        for article in bdn_articles:
            assert article["source"] == "bdn"

    def test_has_author(self, bdn_articles):
        for article in bdn_articles:
            assert "author" in article

    def test_has_required_fields(self, bdn_articles):
        for article in bdn_articles:
            for field in ["title", "url", "summary", "published", "source"]:
                assert field in article

    def test_url_is_bdn(self, bdn_articles):
        for article in bdn_articles:
            assert "bangordailynews.com" in article["url"]


class TestIsUmaineArticle:
    def test_matches_umaine_keyword(self):
        assert _is_umaine_article({"title": "UMaine wins big", "summary": "", "sport": ""})

    def test_matches_black_bears(self):
        assert _is_umaine_article({"title": "Black Bears take the ice", "summary": "", "sport": ""})

    def test_matches_hockey_east_in_sport(self):
        assert _is_umaine_article({"title": "Playoff preview", "summary": "", "sport": "Hockey East"})

    def test_rejects_unrelated(self):
        assert not _is_umaine_article({"title": "Red Sox win", "summary": "Boston baseball", "sport": "MLB"})
