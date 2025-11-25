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
        self.test_dir = Path(__file__).parent
        self.html_file = self.test_dir / "data" / "test_schedule.htm"
        self.response_file = self.test_dir / "data" / "schedule.json"

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
