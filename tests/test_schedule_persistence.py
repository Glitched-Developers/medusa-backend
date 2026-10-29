import pytest

from database import meta, save_schedule, table


@pytest.mark.asyncio
async def test_save_schedule_inserts_and_updates_group(tmp_path, monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine

    test_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'dev.db'}")
    monkeypatch.setattr("database.engine", test_engine)

    async with test_engine.begin() as connection:
        await connection.run_sync(meta.create_all)

    payload = {
        "metadata": {"timestamp": "2026-01-01 12:00:00"},
        "schedule": {"monday": []},
    }
    await save_schedule(123, payload)
    payload["schedule"] = {"tuesday": []}
    await save_schedule(123, payload)

    async with test_engine.connect() as connection:
        rows = (await connection.execute(table.select())).all()

    assert len(rows) == 1
    assert rows[0].group == 123
    assert rows[0].data == '{"tuesday": []}'
    await test_engine.dispose()
