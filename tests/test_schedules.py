"""Tests for schedule_txt parser."""

import os
import pytest
from scraper.schedules import parse_schedule_txt, discover_schedule_id


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def schedule_txt():
    path = os.path.join(FIXTURE_DIR, "schedule_txt_mhockey.txt")
    with open(path) as f:
        return f.read()


class TestParseScheduleTxt:
    def test_returns_dict(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        assert isinstance(result, dict)

    def test_has_record(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        assert "record" in result
        assert "overall" in result["record"]
        assert "conference" in result["record"]

    def test_overall_record_format(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        parts = result["record"]["overall"].split("-")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_has_games_list(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        assert "games" in result
        assert isinstance(result["games"], list)
        assert len(result["games"]) > 0

    def test_game_has_required_fields(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        game = result["games"][0]
        for field in ["date", "time", "home_away", "opponent", "location"]:
            assert field in game, f"Missing field: {field}"

    def test_completed_game_has_result(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        game = result["games"][0]
        assert "result" in game
        assert game["result"] != ""

    def test_home_away_values(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        values = {g["home_away"] for g in result["games"]}
        assert values.issubset({"Home", "Away", "Neutral"})

    def test_result_format(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        completed = [g for g in result["games"] if g.get("result")]
        assert len(completed) > 0
        for g in completed:
            assert g["result"][0] in ("W", "L", "T"), f"Bad result: {g['result']}"

    def test_future_game_has_no_result(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        last = result["games"][-1]
        assert last.get("result", "") == ""

    def test_streak_extracted(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        assert "streak" in result["record"]

    def test_game_count(self, schedule_txt):
        result = parse_schedule_txt(schedule_txt)
        assert len(result["games"]) >= 35

    def test_empty_input_returns_empty(self):
        result = parse_schedule_txt("")
        assert result["games"] == []
