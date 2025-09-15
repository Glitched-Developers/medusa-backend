"""
API module for fetching and parsing class schedules from the bsuedu.ru website.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, TypedDict

import enum
import httpx
import re
from bs4 import BeautifulSoup, NavigableString

from utils import week_validator

# HTTP request headers to bypass server restrictions
HEADERS = {
    'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
    'origin': "https://bsuedu.ru",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    'x-requested-with': "XMLHttpRequest",
}


class WeekActions(enum.Enum):
    """Enumeration of available week selection actions."""
    THIS_WEEK = "this_week"
    NEXT_WEEK = "next_week"
    LAST_WEEK = "last_week"


class Lesson(TypedDict, total=False):
    """Type definition for a lesson entry."""
    number: int
    time: str
    type: str
    name: str
    teacher: str
    auditory: str
    online: bool
    subgroup: Optional[int]
    key: str


class ScheduleResult(TypedDict):
    """Type definition for the schedule result."""
    metadata: Dict[str, str]
    schedule: Dict[str, List[Dict[str, Any]]]


async def fetch_week(action: WeekActions = WeekActions.THIS_WEEK, week = 0) -> int:
    """
    Fetch current week number based on the specified action.

    Args:
        action: Week action to perform (this_week, next_week, last_week)
        week: Base week number (default: 0)

    Returns:
        Week number

    Raises:
        ConnectionError: If there's an issue with the API connection or data is invalid
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://bsuedu.ru/bsu/education/schedule/week/week_json.php?week={week}&act={action.value}",
                headers=HEADERS,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data or not isinstance(data, list):
                raise ValueError("Invalid data format received from API")

            return data[0]
    except (httpx.HTTPError, IndexError, ValueError) as e:
        raise ConnectionError(f"Failed to fetch week data: {str(e)}") from e

def extract_subject_name(name_cell) -> str:
    """
    Extract the subject name from a cell, ignoring <small> tags and other service elements.

    Args:
        name_cell: BeautifulSoup element containing the subject name

    Returns:
        Clean subject name as string
    """
    # If cell contains only one <a> tag and no text around it,
    # use its content as subject name
    if len(name_cell.contents) == 1 and name_cell.a:
        return name_cell.a.get_text(strip=True)

    # If structure is more complex, extract main text
    main_text = ""
    for content in name_cell.contents:
        # Skip small tags, which usually contain additional info
        if isinstance(content, NavigableString):
            main_text += content.strip()
        elif content.name != 'small':
            main_text += content.get_text(strip=True)

    # Remove parentheses with content, which usually contain EUMKD info
    main_text = re.sub(r'\(.*?\)', '', main_text)
    main_text = main_text.strip()

    # If there's no text after processing, look for the first <a> tag
    if not main_text and name_cell.a:
        return name_cell.a.get_text(strip=True)

    return main_text

def process_day_lessons(lessons: List[Lesson]) -> List[Dict[str, Any]]:
    """
    Group subgroups of the same subject into one entry, but only if they occur 
    at the same time and have the same lesson type.

    Args:
        lessons: List of lesson dictionaries for a day

    Returns:
        Processed list of lessons with grouped subgroups
    """
    result = []

    # Group lessons by key - combination of number, time, name and type
    grouped = {}
    for lesson in lessons:
        key = lesson["key"]
        if "subgroup" not in lesson:
            # If not a subgroup, add as is
            result.append({k: v for k, v in lesson.items() if k != "key"})
        else:
            # If it's a subgroup, group for further processing
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(lesson)

    # Process grouped subgroups
    for key, group_lessons in grouped.items():
        if len(group_lessons) == 1:
            # If only one subgroup, add as is
            result.append({k: v for k, v in group_lessons[0].items() if k != "key"})
        else:
            # If multiple subgroups, create hierarchy
            # Sort by subgroup number
            group_lessons.sort(key=lambda x: x.get("subgroup", 999))

            # First subgroup becomes the main one
            main_lesson = {k: v for k, v in group_lessons[0].items() if k != "key"}

            # Add other subgroups as nested
            for sub_lesson in group_lessons[1:]:
                subgroup_num = sub_lesson.get("subgroup", "other")
                sub_data = {
                    "teacher": sub_lesson["teacher"],
                    "auditory": sub_lesson["auditory"],
                    "online": sub_lesson["online"],
                    "subgroup": subgroup_num
                }
                main_lesson[f"subgroup_{subgroup_num}"] = sub_data

            result.append(main_lesson)

    # Sort result by lesson number
    result.sort(key=lambda x: x["number"])
    return result

def parse_schedule(html: str, timestamp: Optional[str] = None) -> ScheduleResult:
    """
    Parse HTML schedule with correct subgroup grouping.

    Args:
        html: HTML content to parse
        timestamp: Timestamp for metadata (default: current time)

    Returns:
        Dictionary with schedule data and metadata
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    soup = BeautifulSoup(html, "html.parser")

    # Use provided metadata
    result: ScheduleResult = {
        "metadata": {
            "timestamp": timestamp
        },
        "schedule": {}
    }

    schedule = {}
    current_day = None

    # For tracking subgroups and rowspan
    current_rowspan = None
    current_rowspan_left = 0

    # For each day, store a list of lessons with their subgroups
    day_lessons: Dict[str, List[Lesson]] = {}

    for row in soup.select("table#shedule tr"):
        # Determine day
        day_header = row.find("td", class_="colspan")
        if day_header:
            # Process previous day if exists
            if current_day and day_lessons.get(current_day):
                schedule[current_day] = process_day_lessons(day_lessons[current_day])

            # Create new day
            day_text = day_header.get_text(strip=True)
            current_day = day_text
            if current_day not in day_lessons:
                day_lessons[current_day] = []

            # Reset rowspan for new day
            current_rowspan = None
            current_rowspan_left = 0
            continue

        # If day is not defined yet, skip row
        if not current_day:
            continue

        columns = row.find_all("td")
        if len(columns) < 3:  # At minimum there should be number, time, and type
            continue

        # Check for rowspan - determine if row belongs to previous pair
        num_cell = row.find("td", id="num")
        time_cell = row.find("td", id="time")

        if num_cell and time_cell:
            # New pair
            current_rowspan_left = 0
            current_rowspan = None

            # Get number and time
            number_text = num_cell.get_text(strip=True)
            num_match = re.search(r'(\d+)', number_text)
            number = int(num_match.group(1)) if num_match else 0
            time = time_cell.get_text(strip=True)

            # Check for rowspan for future processing
            rowspan_num = num_cell.get('rowspan')
            if rowspan_num:
                current_rowspan = {
                    'number': number,
                    'time': time,
                    'rows': int(rowspan_num)
                }
                current_rowspan_left = current_rowspan['rows'] - 1
        else:
            # This might be a row related to previous pair through rowspan
            if current_rowspan and current_rowspan_left > 0:
                number = current_rowspan['number']
                time = current_rowspan['time']
                current_rowspan_left -= 1
            else:
                # If not rowspan and no number and time, skip
                continue

        # Extract information about the pair
        type_cell = row.find("td", id="lesson")
        name_cell = row.select_one("td[id='lesson'][style='border-left:none;']")
        teacher_cell = row.find("td", id="teacher")
        auditory_cell = row.find("td", id="aud")

        if not all([type_cell, name_cell, teacher_cell, auditory_cell]):
            continue

        # Get lesson type
        lesson_type = type_cell.get_text(strip=True)
        if "лек" in lesson_type:
            lesson_type = "лекция"
        elif "пр.з" in lesson_type:
            lesson_type = "пз"
        elif "лаб" in lesson_type:
            lesson_type = "лабораторная"
        elif "пер" in lesson_type:
            lesson_type = "пересдача"
        elif "конс" in lesson_type:
            lesson_type = "консультация"
        elif "экз." in lesson_type:
            lesson_type = "экзамен"
        elif "зач." in lesson_type:
            lesson_type = "зачёт"
        elif "дифф.зач." in lesson_type:
            lesson_type = "дифф"
        else:
            lesson_type = lesson_type.capitalize()

        # Get subject name
        name = extract_subject_name(name_cell)

        # Determine subgroup
        subgroup = None
        name_text = name_cell.get_text(strip=True)
        subgroup_match = re.search(r'п/г\s*(\d+)', name_text) or re.search(r'(\d+)\s*подгруппа', name_text)
        if subgroup_match:
            subgroup = int(subgroup_match.group(1))

        # Get teacher
        teacher_text = teacher_cell.get_text(strip=True)
        teacher = re.sub(r'^преп\.', '', teacher_text).strip()

        # Get auditory and online information
        auditory = auditory_cell.get_text(strip=True)
        online = "Для студентов с возможностью подключиться он-лайн" in auditory or \
                 "Для студентов с возможностью подключиться онлайн" in auditory

        # Create lesson entry
        lesson: Lesson = {
            "number": number,
            "time": time,
            "type": lesson_type,
            "name": name.replace("_", ""),
            "teacher": teacher,
            "auditory": auditory.replace("Для студентов с возможностью подключиться он-лайн", "")
            .replace("Для студентов с возможностью подключиться онлайн", "").strip(),
            "online": online,
            "key": f"{number}_{time}_{name}_{lesson_type}",
        }

        if subgroup:
            lesson["subgroup"] = subgroup

        # Add lesson to the list for current day
        day_lessons[current_day].append(lesson)

    # Process last day
    if current_day and day_lessons.get(current_day):
        schedule[current_day] = process_day_lessons(day_lessons[current_day])

    result["schedule"] = schedule

    return result

async def fetch_schedule(week: Optional[str] = None, group: int = 90002493) -> ScheduleResult:
    """
    Fetch and parse the schedule for a specific week and group.

    Args:
        week: Week number (default: current week)
        group: Group ID (default: 90002493)

    Returns:
        Dictionary with parsed schedule data and metadata
    """
    if week is None:
        week = str(await fetch_week())

    week_validator(week)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://bsuedu.ru/bsu/education/schedule/groups/show_schedule.php?group={group}&week={week}",
                headers=HEADERS,
                timeout=10
            )
            response.raise_for_status()
            data = response.text

            return parse_schedule(
                data,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
    except (httpx.HTTPError, IndexError, ValueError) as e:
        raise ConnectionError(f"Failed to fetch week data: {str(e)}") from e
