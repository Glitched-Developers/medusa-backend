"""
Test for HTML schedule parsing functionality
"""
import json
from pathlib import Path

import pytest

from api import parse_schedule


class TestScheduleParsing:
    """Test cases for HTML schedule parsing functionality"""

    def setup_method(self):
        """Set up test data paths"""
        self.project_root = Path(__file__).parent.parent
        self.html_file = self.project_root / "page.html"
        self.response_file = self.project_root / "response.json"

    def test_parse_html_vs_expected_response(self):
        """
        Test that parsing page.html produces the same result as response.json

        This test:
        1. Reads HTML from page.html
        2. Parses it using parse_schedule function
        3. Compares the result with expected response.json
        4. Fails if they don't match
        """
        # Read test data files
        if not self.html_file.exists():
            pytest.skip(f"Test data file not found: {self.html_file}")

        if not self.response_file.exists():
            pytest.skip(f"Expected response file not found: {self.response_file}")

        # Read HTML content
        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Read expected response
        with open(self.response_file, 'r', encoding='utf-8') as f:
            expected_response = json.load(f)

        # Parse HTML using the production parser
        actual_result = parse_schedule(html_content, timestamp="2025-09-15 21:22:22")

        # Compare results
        assert actual_result == expected_response, (
            f"Parsed HTML does not match expected response.\n"
            f"Expected keys: {set(expected_response.keys())}\n"
            f"Actual keys: {set(actual_result.keys())}\n"
            f"Differences in metadata: {self._dict_diff(expected_response.get('metadata', {}), actual_result.get('metadata', {}))}\n"
            f"Differences in schedule: {self._dict_diff(expected_response.get('schedule', {}), actual_result.get('schedule', {}))}"
        )

    def test_parse_html_structure(self):
        """Test that parsed HTML has the expected structure"""
        if not self.html_file.exists():
            pytest.skip(f"Test data file not found: {self.html_file}")

        # Read HTML content
        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Parse HTML
        result = parse_schedule(html_content)

        # Verify structure
        assert "metadata" in result, "Result should contain metadata"
        assert "schedule" in result, "Result should contain schedule"
        assert "timestamp" in result["metadata"], "Metadata should contain timestamp"
        assert isinstance(result["schedule"], dict), "Schedule should be a dictionary"

        # Verify schedule contains expected keys (dates)
        schedule_days = list(result["schedule"].keys())
        assert len(schedule_days) > 0, "Schedule should contain at least one day"

        # Verify each day has the expected structure
        for day, lessons in result["schedule"].items():
            assert isinstance(lessons, list), f"Lessons for {day} should be a list"

            for lesson in lessons:
                # Verify required lesson fields
                required_fields = ["number", "time", "type", "name", "teacher", "auditory", "online"]
                for field in required_fields:
                    assert field in lesson, f"Lesson should contain field: {field}"

                # Verify field types
                assert isinstance(lesson["number"], int), "Lesson number should be integer"
                assert isinstance(lesson["time"], str), "Lesson time should be string"
                assert isinstance(lesson["type"], str), "Lesson type should be string"
                assert isinstance(lesson["name"], str), "Lesson name should be string"
                assert isinstance(lesson["teacher"], str), "Lesson teacher should be string"
                assert isinstance(lesson["auditory"], str), "Lesson auditory should be string"
                assert isinstance(lesson["online"], bool), "Lesson online flag should be boolean"

    def test_parse_with_custom_timestamp(self):
        """Test parsing with custom timestamp"""
        if not self.html_file.exists():
            pytest.skip(f"Test data file not found: {self.html_file}")

        # Read HTML content
        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        custom_timestamp = "2025-09-10 12:34:56"
        result = parse_schedule(html_content, timestamp=custom_timestamp)

        assert result["metadata"]["timestamp"] == custom_timestamp, (
            f"Custom timestamp should be preserved. Expected: {custom_timestamp}, "
            f"Got: {result['metadata']['timestamp']}"
        )

    def _dict_diff(self, dict1: dict, dict2: dict) -> dict:
        """Helper method to find differences between two dictionaries"""
        diff = {}

        # Keys in dict1 but not in dict2
        for key in set(dict1.keys()) - set(dict2.keys()):
            diff[f"missing_in_second_{key}"] = dict1[key]

        # Keys in dict2 but not in dict1
        for key in set(dict2.keys()) - set(dict1.keys()):
            diff[f"missing_in_first_{key}"] = dict2[key]

        # Values that differ
        for key in set(dict1.keys()) & set(dict2.keys()):
            if dict1[key] != dict2[key]:
                diff[f"different_{key}"] = {"expected": dict1[key], "actual": dict2[key]}

        return diff