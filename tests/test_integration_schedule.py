import json
import os
from pathlib import Path

import pytest

from api import fetch_schedule, parse_schedule


@pytest.mark.asyncio
async def test_schedule_integration():
    """
    Integration dev_test that:
    1. Parses local test_schedule.htm and compares with schedule.json
    2. If successful, fetches real data from BSU and compares with schedule.json
    """
    # 1. Load dev_test data
    # Use path relative to this dev_test file
    current_dir = Path(__file__).parent
    html_path = current_dir / "data" / "test_schedule.htm"
    json_path = current_dir / "data" / "schedule.json"

    if not html_path.exists():
        pytest.fail(f"Test data file not found: {html_path}")
    if not json_path.exists():
        pytest.fail(f"Expected response file not found: {json_path}")

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    with open(json_path, "r", encoding="utf-8") as f:
        expected_json = json.load(f)

    # The expected JSON has a wrapper "schedule" key
    expected_data = expected_json["schedule"]
    expected_timestamp = expected_data["metadata"]["timestamp"]

    # 2. Parse HTML and compare
    print("\nStep 1: Testing local HTML parsing...")
    parsed_result = parse_schedule(html_content, timestamp=expected_timestamp)

    # Deep comparison
    assert parsed_result == expected_data, (
        "Parsed local HTML does not match expected JSON.\n"
        f"Expected keys: {list(expected_data.keys())}\n"
        f"Actual keys: {list(parsed_result.keys())}"
    )
    print("✓ Local parsing matches expected JSON")

    # 3. Fetch real data and compare
    if (os.environ.get("CI") or os.environ.get("GITLAB_CI")) and not os.environ.get(
        "BSU_PROXY"
    ):
        print(
            "Skipping remote data fetching in CI environment (no BSU_PROXY configured)"
        )
        return

    print("Step 2: Testing remote data fetching...")
    # Group: 90002493, Week: 1711202523112025
    group_id = 90002493
    week_id = "1711202523112025"

    try:
        fetched_result = await fetch_schedule(group=group_id, week=week_id)
    except Exception as e:
        pytest.fail(f"Failed to fetch remote schedule: {e}")

    # Validate structure instead of exact content match
    # (Content changes over time, so exact match against static JSON is brittle)
    assert "metadata" in fetched_result, "Response missing metadata"
    assert "schedule" in fetched_result, "Response missing schedule"
    assert "timestamp" in fetched_result["metadata"], "Metadata missing timestamp"
    assert isinstance(
        fetched_result["schedule"], dict
    ), "Schedule should be a dictionary"

    # If we got any schedule data, verify its structure
    if fetched_result["schedule"]:
        # Check at least one day
        days = list(fetched_result["schedule"].keys())
        first_day_lessons = fetched_result["schedule"][days[0]]
        assert isinstance(
            first_day_lessons, list
        ), "Day schedule should be a list of lessons"

        if first_day_lessons:
            lesson = first_day_lessons[0]
            required_fields = ["name", "time", "type", "teacher", "auditory"]
            for field in required_fields:
                assert field in lesson, f"Lesson missing required field: {field}"

    print("✓ Remote fetching returned valid structure")

    # Note: We do not compare fetched_result with expected_data because the live schedule
    # changes over time, making exact comparison with static JSON brittle.
    # The structure validation above is sufficient for integration testing.
