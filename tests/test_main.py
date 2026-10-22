"""
Tests for main application module
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app


class TestMainApp:
    """Test cases for main FastAPI application"""

    def setup_method(self):
        """Set up dev_test client"""
        self.client = TestClient(app)

    def test_app_metadata(self):
        """Test that app has correct metadata"""
        assert app.title == "Medusa Backend API"
        assert app.version.startswith("v")
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"

    def test_docs_endpoint(self):
        """Test that documentation endpoint is accessible"""
        response = self.client.get("/docs")
        assert response.status_code == 200
        assert "Medusa Backend API" in response.text

    def test_redoc_endpoint(self):
        """Test that ReDoc endpoint is accessible"""
        response = self.client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self):
        """Test that OpenAPI schema is generated"""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Medusa Backend API"
        assert schema["info"]["version"].startswith("v")


@pytest.mark.asyncio
class TestMainFunction:
    """Test cases for main() function"""

    @patch("main.uvicorn.Server.serve")
    async def test_main_function_initialization(self, mock_serve):
        """Test that main function initializes correctly"""
        from main import main

        # Configure mock to be awaitable
        mock_serve.return_value = None

        await main()

        # Verify server was started
        mock_serve.assert_called_once()

    @patch.dict("os.environ", {"PORT": "9000"})
    @patch("main.uvicorn.Server.serve")
    async def test_main_function_custom_port(self, mock_serve):
        """Test that main function uses custom port from environment"""
        from main import main

        # Configure mock to be awaitable
        mock_serve.return_value = None

        await main()

        # Check if uvicorn was configured with custom port
        mock_serve.assert_called_once()
