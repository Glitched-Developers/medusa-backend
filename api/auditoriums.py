"""Crawl and parse the BSU auditorium directory and room schedules.

The public directory lives at ``/auditories/``. Each building is a ``<select
name="build">`` option; rooms for a building come from ``aud_json.php`` as a
list of ``[id, name]`` pairs. A room schedule is the same HTML table the group
schedule uses, served by ``auditories/index.php?auditory={id}``.
"""

import asyncio
import os
import re
import traceback
import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException
from loguru import logger
from pybreaker import CircuitBreakerError

from api import (
    HEADERS,
    RETRY_DELAY,
    UPSTREAM_RETRIES,
    UPSTREAM_TIMEOUT,
    parse_schedule,
)
from api.circuit_breaker import bsu_breaker
from utils import week_validator

BASE_URL = "https://bsuedu.ru/bsu/education/schedule/auditories"
BUILD_BATCH = 6

# "6-7 (12 к.)", "6-7 12 корпус", "5-2 13к", "5-3-1 15к".
# The building marker may sit inside parentheses: "6-12 (Учебный корпус №15)".
_ROOM = re.compile(r"(?P<room>\d+(?:-\d+)+)")
# "12 корпус", "12к", "12 к.", "(12 к.)", "корпус №15".
# Cyrillic is matched by script so the pattern does not depend on the
# source-file encoding flag.
_CYR = r"\u0400-\u04FF"
_BUILDING = re.compile(
    rf"(?:[{_CYR}]{{5,}}\s*\u2116?\s*(\d+)"
    rf"|(\d+)\s*[{_CYR}]{{5,}}"
    rf"|(\d+)\s*[{_CYR}](?:$|[^\w]))"
)


def _building_number(text: str) -> str | None:
    """First building number in ``text``, or None when the text has none."""
    found = _BUILDING.search(text)
    if found is None:
        return None
    return next(group for group in found.groups() if group)


def normalize_auditorium_name(name: str, building: str | None = None) -> str:
    """Fold a published room name into ``{room}_{building}``.

    Examples:
        ``6-7 12 корпус`` -> ``6-7_12``
        ``6-7 (12 к.)`` -> ``6-7_12``
        ``5-2 13к`` -> ``5-2_13``
        ``5-3-1 15к`` -> ``5-3-1_15``

    ``building`` is used when the name itself has no building number, which is
    how the schedule cell writes a room (``5-0-3, Учебный корпус №15``).
    Names that are not a numbered room are collapsed to a single token.
    """
    text = " ".join(name.split())
    match = _ROOM.search(text)
    if match is None:
        return re.sub(r"\s+", "_", text).strip("_")

    room = match.group("room")
    # Look for the building only after the room number, so a leading floor
    # digit is not mistaken for a building.
    building_number = _building_number(text[match.end() :])
    if building_number is None and building:
        building_number = _building_number(building)
        if building_number is None:
            digits = re.search(r"\d+", building)
            building_number = digits.group(0) if digits else None
    return f"{room}_{building_number}" if building_number else room


def parse_building_ids(html: str) -> list[str]:
    """Read building option values from the auditorium directory page."""
    soup = BeautifulSoup(html, "html.parser")
    select = soup.find("select", attrs={"name": "build"})
    if select is None:
        return []
    ids = []
    for option in select.find_all("option"):
        value = (option.get("value") or "").strip()
        if value and value != "0":
            ids.append(value)
    return ids


def parse_auditorium_rows(payload, building: str | None = None) -> dict[str, dict]:
    """Turn one building's JSON into ``{id: {id, name, token}}``.

    A bad payload yields an empty map. One building must not fail the crawl.
    """
    rows: dict[str, dict] = {}
    if not isinstance(payload, list):
        return rows
    for item in payload:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        room_id = str(item[0]).strip()
        name = str(item[1]).strip()
        if not room_id or not name:
            continue
        rows[room_id] = {
            "id": room_id,
            "name": name,
            "token": normalize_auditorium_name(name, building),
        }
    return rows


async def _get_json(client: httpx.AsyncClient, url: str):
    response = await client.get(url, headers=HEADERS, timeout=UPSTREAM_TIMEOUT)
    response.raise_for_status()
    return response.json()


async def _get_text(client: httpx.AsyncClient, url: str, params: dict | None = None) -> str:
    response = await client.get(
        url, params=params, headers=HEADERS, timeout=UPSTREAM_TIMEOUT
    )
    response.raise_for_status()
    return response.text


async def _with_retries(action):
    last_error: Exception | None = None
    for attempt in range(UPSTREAM_RETRIES):
        try:
            return await action()
        except httpx.HTTPError as error:
            last_error = error
            if attempt == UPSTREAM_RETRIES - 1:
                raise
            await asyncio.sleep(RETRY_DELAY * (2**attempt))
    raise last_error  # pragma: no cover - the loop either returns or raises


async def _rooms_for_building(
    client: httpx.AsyncClient, building: str
) -> dict[str, dict]:
    try:
        payload = await _with_retries(
            lambda: _get_json(client, f"{BASE_URL}/aud_json.php?build={building}")
        )
    except httpx.HTTPError:
        logger.warning(f"Auditorium building {building} did not respond")
        return {}
    return parse_auditorium_rows(payload, building)


async def fetch_auditorium_directory() -> list[dict]:
    """Crawl every building and return auditorium rows.

    Buildings that come back empty are retried once, one at a time. A building
    that still fails is skipped; a crawl with no rooms at all raises
    ``ConnectionError``.
    """
    proxy = os.environ.get("BSU_PROXY")

    @bsu_breaker
    async def _crawl():
        async with httpx.AsyncClient(proxy=proxy) as client:
            html = await _with_retries(lambda: _get_text(client, f"{BASE_URL}/"))
            buildings = parse_building_ids(html)
            if not buildings:
                raise ValueError("Auditorium page has no buildings")

            found: dict[str, dict] = {}
            empty: list[str] = []
            for offset in range(0, len(buildings), BUILD_BATCH):
                batch = buildings[offset : offset + BUILD_BATCH]
                chunks = await asyncio.gather(
                    *(_rooms_for_building(client, building) for building in batch)
                )
                for building, chunk in zip(batch, chunks):
                    if chunk:
                        found.update(chunk)
                    else:
                        empty.append(building)

            for building in empty:
                found.update(await _rooms_for_building(client, building))
            return list(found.values())

    try:
        rows = await _crawl()
    except CircuitBreakerError as error:
        logger.error(f"Circuit breaker is open for BSU upstream: {error}")
        raise ConnectionError(
            "BSU upstream is temporarily unavailable (circuit breaker open)"
        ) from error
    except (httpx.HTTPError, ValueError) as error:
        logger.error(
            f"Failed to crawl auditoriums: {type(error).__name__}: {error}\n"
            f"{traceback.format_exc()}"
        )
        raise ConnectionError(f"Failed to crawl auditoriums: {error!r}") from error

    if not rows:
        raise ConnectionError("BSU returned no auditoriums")
    rows.sort(key=lambda row: (row["token"], row["id"]))
    return rows


async def fetch_auditorium_schedule(auditorium_id: str, week: str) -> dict:
    """Fetch and parse one room's week schedule.

    The page is the same table ``parse_schedule`` already understands. The
    upstream call follows the retries and circuit breaker used for groups.
    """
    week_validator(week)
    proxy = os.environ.get("BSU_PROXY")
    url = f"{BASE_URL}/index.php"

    @bsu_breaker
    async def _fetch() -> str:
        async with httpx.AsyncClient(proxy=proxy) as client:
            return await _with_retries(
                lambda: _get_text(
                    client, url, {"auditory": auditorium_id, "week": week}
                )
            )

    try:
        html = await _fetch()
    except HTTPException:
        raise
    except CircuitBreakerError as error:
        logger.error(f"Circuit breaker is open for BSU upstream: {error}")
        raise ConnectionError(
            "BSU upstream is temporarily unavailable (circuit breaker open)"
        ) from error
    except httpx.HTTPError as error:
        logger.error(
            f"Failed to fetch auditorium schedule: {type(error).__name__}: {error}\n"
            f"{traceback.format_exc()}"
        )
        raise ConnectionError(
            f"Failed to fetch auditorium schedule: {error!r}"
        ) from error

    if 'id="shedule"' not in html and "id='shedule'" not in html:
        raise LookupError(f"Аудитория не найдена: {auditorium_id}")
    return parse_schedule(html)



