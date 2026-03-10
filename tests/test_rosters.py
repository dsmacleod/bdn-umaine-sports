"""Tests for Sidearm roster parser."""

import os

import pytest

from scraper.rosters import parse_roster

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def roster_html():
    path = os.path.join(FIXTURE_DIR, "roster_mhockey.html")
    with open(path) as f:
        return f.read()


@pytest.fixture
def players(roster_html):
    return parse_roster(roster_html)


class TestParseRoster:
    def test_returns_list(self, players):
        assert isinstance(players, list)

    def test_has_players(self, players):
        assert len(players) > 0

    def test_no_duplicates(self, players):
        ids = [p["player_id"] for p in players]
        assert len(ids) == len(set(ids)), "Duplicate player_ids found"

    def test_player_has_required_fields(self, players):
        required = ["player_id", "name", "number", "position", "year", "hometown"]
        for player in players:
            for field in required:
                assert field in player, (
                    f"Missing field '{field}' for player {player.get('name', '?')}"
                )

    def test_player_name_not_empty(self, players):
        for player in players:
            assert player["name"], (
                f"Empty name for player_id={player['player_id']}"
            )

    def test_number_is_string(self, players):
        for player in players:
            assert isinstance(player["number"], str), (
                f"Number should be str, got {type(player['number'])} "
                f"for {player['name']}"
            )

    def test_has_headshot(self, players):
        with_headshot = [p for p in players if p.get("headshot")]
        assert len(with_headshot) > 0, "Expected at least some players to have headshots"

    def test_empty_html(self):
        assert parse_roster("") == []
