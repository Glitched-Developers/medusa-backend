import pytest
from fastapi import HTTPException

from routes import refresh_schedule


@pytest.mark.asyncio
async def test_refresh_requires_admin_token(monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "secret")
    with pytest.raises(HTTPException) as error:
        await refresh_schedule(123, authorization="Bearer wrong")
    assert error.value.status_code == 401
