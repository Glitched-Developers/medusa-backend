"""
Test configuration and fixtures for Medusa Backend tests
"""

import asyncio
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the dev session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
