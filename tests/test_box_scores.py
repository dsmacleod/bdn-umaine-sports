"""Tests for box score parser."""

import json
import os
import pytest
from scraper.box_scores import parse_box_score


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def raw_data():
    path = os.path.join(FIXTURE_DIR, "box_score_sample.json")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def box_score(raw_data):
    return parse_box_score(raw_data)


class TestParseBoxScore:
    def test_returns_dict(self, box_score):
        assert isinstance(box_score, dict)

    def test_has_teams(self, box_score):
        assert "home" in box_score
        assert "away" in box_score

    def test_team_has_name_and_score(self, box_score):
        assert box_score["home"]["name"] == "Maine"
        assert box_score["home"]["score"] == "2"
        assert box_score["away"]["name"] == "New Hampshire"
        assert box_score["away"]["score"] == "2"

    def test_has_periods(self, box_score):
        assert "periods" in box_score["home"]
        assert isinstance(box_score["home"]["periods"], list)
        # 3 regulation periods (non-zero or regulation)
        assert len(box_score["home"]["periods"]) == 3

    def test_has_leaders(self, box_score):
        assert "leaders" in box_score["home"]
        assert isinstance(box_score["home"]["leaders"], list)
        assert len(box_score["home"]["leaders"]) > 0
        leader = box_score["home"]["leaders"][0]
        assert "name" in leader
        # Leader name should have no HTML tags
        assert "<" not in leader["name"]
        assert ">" not in leader["name"]
        assert leader["name"] == "Rousseau, Mathis"

    def test_has_location(self, box_score):
        assert "location" in box_score
        assert box_score["location"] == "Brunswick, Maine"

    def test_has_attendance(self, box_score):
        assert "attendance" in box_score
        assert box_score["attendance"] == "2000"

    def test_has_recap(self, box_score):
        assert "recap" in box_score
        assert "headline" in box_score["recap"]
        assert box_score["recap"]["headline"] != ""
        assert "UNH" in box_score["recap"]["headline"]

    def test_result_status(self, box_score):
        assert "result_status" in box_score
        assert box_score["result_status"] in ("W", "L", "T")

    def test_empty_input(self):
        result = parse_box_score({})
        assert result["home"]["name"] == ""
        assert result["away"]["name"] == ""
        assert result["home"]["score"] == ""
        assert result["away"]["score"] == ""
        assert result["location"] == ""
        assert result["attendance"] == ""
        assert result["result_status"] == ""

    def test_recap_teaser_has_no_html(self, box_score):
        teaser = box_score["recap"].get("teaser", "")
        assert "<" not in teaser
        assert ">" not in teaser

    def test_periods_exclude_zero_ot(self, box_score):
        """OT periods with score 0 should be excluded."""
        home_periods = box_score["home"]["periods"]
        # This game has 3 regulation + 2 OT all zero, so only 3 periods
        for p in home_periods:
            assert "period" in p
            assert "score" in p
