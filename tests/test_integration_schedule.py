import json
import pytest
from pathlib import Path
from api import parse_schedule, fetch_schedule

@pytest.mark.asyncio
async def test_schedule_integration():
    """
    Integration test that:
    1. Parses local test_schedule.htm and compares with schedule.json
    2. If successful, fetches real data from BSU and compares with schedule.json
    """
    # 1. Load test data
    # Use path relative to this test file
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
    print("Step 2: Testing remote data fetching...")
    # Group: 90002493, Week: 1711202523112025
    group_id = 90002493
    week_id = "1711202523112025"
    
    try:
        fetched_result = await fetch_schedule(group=group_id, week=week_id)
    except Exception as e:
        pytest.fail(f"Failed to fetch remote schedule: {e}")
    
    # Prepare for comparison (ignore timestamp)
    fetched_result_no_ts = fetched_result.copy()
    fetched_result_no_ts["metadata"] = fetched_result["metadata"].copy()
    fetched_result_no_ts["metadata"].pop("timestamp", None)
    
    expected_data_no_ts = expected_data.copy()
    expected_data_no_ts["metadata"] = expected_data["metadata"].copy()
    expected_data_no_ts["metadata"].pop("timestamp", None)
    
    assert fetched_result_no_ts == expected_data_no_ts, (
        "Fetched remote data does not match expected JSON (excluding timestamp).\n"
        "This might indicate that the schedule on the website has changed since schedule.json was generated."
    )
    print("✓ Remote fetching matches expected JSON")
