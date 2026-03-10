"""Tests for standings parsers (America East JSON + Hockey East HTML)."""

import json
import os

import pytest

from scraper.standings import parse_america_east, parse_hockey_east

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


# ── America East fixtures ─────────────────────────────────────────────


@pytest.fixture
def ae_data():
    path = os.path.join(FIXTURE_DIR, "ae_standings_mbball.json")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def ae_result(ae_data):
    return parse_america_east(ae_data)


# ── Hockey East fixtures ──────────────────────────────────────────────


@pytest.fixture
def he_html():
    path = os.path.join(FIXTURE_DIR, "he_standings_men.html")
    with open(path) as f:
        return f.read()


@pytest.fixture
def he_result(he_html):
    return parse_hockey_east(he_html)


# ── TestParseAmericaEast ──────────────────────────────────────────────


class TestParseAmericaEast:
    def test_returns_dict(self, ae_result):
        assert isinstance(ae_result, dict)

    def test_has_teams(self, ae_result):
        assert isinstance(ae_result["teams"], list)
        assert len(ae_result["teams"]) > 0

    def test_has_title(self, ae_result):
        assert "title" in ae_result
        assert ae_result["title"]  # non-empty

    def test_team_has_required_fields(self, ae_result):
        team = ae_result["teams"][0]
        for field in ["school", "conference", "overall", "pct", "streak"]:
            assert field in team, f"Missing field: {field}"

    def test_school_name_is_clean(self, ae_result):
        for team in ae_result["teams"]:
            assert "<" not in team["school"], (
                f"HTML tag found in school name: {team['school']}"
            )
            assert ">" not in team["school"], (
                f"HTML tag found in school name: {team['school']}"
            )

    def test_clinch_markers_stripped(self, ae_result):
        for team in ae_result["teams"]:
            assert " -x" not in team["school"], (
                f"Clinch marker found: {team['school']}"
            )
            assert " -y" not in team["school"], (
                f"Clinch marker found: {team['school']}"
            )
            assert " -z" not in team["school"], (
                f"Clinch marker found: {team['school']}"
            )

    def test_maine_present(self, ae_result):
        schools = [t["school"] for t in ae_result["teams"]]
        assert "Maine" in schools

    def test_is_umaine_flag(self, ae_result):
        umaine_teams = [t for t in ae_result["teams"] if t.get("is_umaine")]
        assert len(umaine_teams) == 1
        assert umaine_teams[0]["school"] == "Maine"

    def test_teams_sorted_by_standing(self, ae_result):
        pcts = [float(t["pct"]) for t in ae_result["teams"]]
        assert pcts == sorted(pcts, reverse=True)

    def test_empty_input(self):
        result = parse_america_east({})
        assert result["teams"] == []


# ── TestParseHockeyEast ───────────────────────────────────────────────


class TestParseHockeyEast:
    def test_returns_dict(self, he_result):
        assert isinstance(he_result, dict)

    def test_has_teams(self, he_result):
        assert len(he_result["teams"]) == 11

    def test_team_has_conference_stats(self, he_result):
        team = he_result["teams"][0]
        for field in ["gp", "pts", "w", "l", "t", "ow", "ol", "sw", "gf", "ga"]:
            assert field in team.get("conference", {}), (
                f"Missing conference field: {field}"
            )

    def test_team_has_overall_stats(self, he_result):
        team = he_result["teams"][0]
        for field in ["gp", "w", "l", "t", "gf", "ga"]:
            assert field in team.get("overall", {}), (
                f"Missing overall field: {field}"
            )

    def test_maine_present(self, he_result):
        schools = [t["school"] for t in he_result["teams"]]
        assert "Maine" in schools

    def test_is_umaine_flag(self, he_result):
        umaine_teams = [t for t in he_result["teams"] if t.get("is_umaine")]
        assert len(umaine_teams) == 1
        assert umaine_teams[0]["school"] == "Maine"

    def test_rank_is_int_or_none(self, he_result):
        for team in he_result["teams"]:
            assert isinstance(team["rank"], (int, type(None))), (
                f"Rank should be int or None, got {type(team['rank'])}: {team['rank']}"
            )

    def test_first_team_has_most_points(self, he_result):
        pts_values = [t["conference"]["pts"] for t in he_result["teams"]]
        assert pts_values[0] == max(pts_values)

    def test_empty_html(self):
        result = parse_hockey_east("")
        assert result["teams"] == []
