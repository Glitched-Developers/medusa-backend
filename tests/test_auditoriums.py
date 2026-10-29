from datetime import datetime, timedelta, timezone

import pytest

from api.auditoriums import (
    normalize_auditorium_name,
    parse_auditorium_rows,
    parse_building_ids,
)
from tasks.auditoriums import _due


@pytest.mark.parametrize(
    ("name", "building", "expected"),
    [
        ("6-7 12 корпус", None, "6-7_12"),
        ("6-7 (12 к.)", None, "6-7_12"),
        ("5-2 13к", None, "5-2_13"),
        ("5-3-1 15к", None, "5-3-1_15"),
        ("5-0-3", "Учебный корпус №15", "5-0-3_15"),
        ("6-12 (Учебный корпус №15)", None, "6-12_15"),
        ("  6-7   12   корпус ", None, "6-7_12"),
    ],
)
def test_normalize_auditorium_name(name, building, expected):
    assert normalize_auditorium_name(name, building) == expected


def test_names_without_a_room_number_collapse_to_one_token():
    assert normalize_auditorium_name("Спортивный зал") == "Спортивный_зал"


def test_parse_building_ids_skips_the_empty_option():
    html = """
    <select name="build">
      <option value="0">Корпус</option>
      <option value="12">12</option>
      <option value="">пусто</option>
      <option value="15">15</option>
    </select>
    """
    assert parse_building_ids(html) == ["12", "15"]


def test_parse_auditorium_rows_drops_malformed_items():
    payload = [
        ["9700", "5-0-3 15к"],
        ["", "без id"],
        ["1"],
        "мусор",
        [9701, "6-7 (12 к.)"],
    ]
    rows = parse_auditorium_rows(payload)
    assert rows == {
        "9700": {"id": "9700", "name": "5-0-3 15к", "token": "5-0-3_15"},
        "9701": {"id": "9701", "name": "6-7 (12 к.)", "token": "6-7_12"},
    }


def test_a_building_payload_that_is_not_a_list_is_empty():
    assert parse_auditorium_rows({"error": 1}) == {}


def test_directory_is_due_when_missing_or_a_month_old():
    now = datetime(2026, 10, 29, tzinfo=timezone.utc)
    assert _due(None, now) is True
    assert _due(now - timedelta(days=29), now) is False
    assert _due(now - timedelta(days=30), now) is True
    assert _due(now.replace(tzinfo=None) - timedelta(days=31), now) is True
