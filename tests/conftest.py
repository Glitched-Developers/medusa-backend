"""
Test configuration and fixtures for Medusa Backend tests
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock database for testing"""
    # This will be expanded when we have actual database models
    pass


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing"""
    return {
        "group": "ПИ-20",
        "date": "2024-01-15",
        "lessons": [
            {
                "time": "08:30-10:00",
                "subject": "Математика",
                "teacher": "Иванов И.И.",
                "room": "305"
            }
        ]
    }