import enum
from datetime import datetime

import httpx
import re
from bs4 import BeautifulSoup, NavigableString

bypass = {
    'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
    'origin': "https://bsuedu.ru",
    'referer': "https://bsuedu.ru/bsu/education/schedule/groups/index.php?group=90002493",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    'x-requested-with': "XMLHttpRequest",
}

class WeekActions(enum.Enum):
    this_week = "this_week"
    next_week = "next_week"
    prev_week = "prev_week"
    last_week = "last_week"


def get_week(act: WeekActions = WeekActions.this_week, week: int = 0) :
    return httpx.get(f"https://bsuedu.ru/bsu/education/schedule/week/week_json.php?week={week}&act={act.value}", headers=bypass).json()[0]
def get_schedule(week: int = get_week(), group:int = 90002493):
    raw = httpx.post(
        f"https://bsuedu.ru/bsu/education/schedule/groups/show_schedule.php?group={group}&week={week}",
        headers=bypass).text

    def parse_schedule(html, user_login="shizamuru-dev", timestamp="2025-04-12 21:50:22"):
        """
        Парсит HTML-расписание с корректной группировкой подгрупп
        """
        soup = BeautifulSoup(html, "html.parser")

        # Используем переданные метаданные
        result = {
            "metadata": {
                "timestamp": timestamp,
                "user_login": user_login
            }
        }

        schedule = {}
        current_day = None

        # Для отслеживания подгрупп и rowspan
        rowspans = {}
        current_rowspan = None
        current_rowspan_left = 0

        # Для каждого дня храним список занятий с их подгруппами
        day_lessons = {}

        for row_idx, row in enumerate(soup.select("table#shedule tr")):
            # Определяем день
            day_header = row.find("td", class_="colspan")
            if day_header:
                # Обрабатываем предыдущий день если есть
                if current_day and day_lessons.get(current_day):
                    schedule[current_day] = process_day_lessons(day_lessons[current_day])

                # Создаем новый день
                day_text = day_header.get_text(strip=True)
                current_day = day_text
                if current_day not in day_lessons:
                    day_lessons[current_day] = []

                # Сбрасываем rowspan для нового дня
                current_rowspan = None
                current_rowspan_left = 0
                continue

            # Если день еще не определен, пропускаем строку
            if not current_day:
                continue

            columns = row.find_all("td")
            if len(columns) < 3:  # Минимум должно быть номер, время и тип
                continue

            # Проверка на rowspan - определяем, принадлежит ли строка к предыдущей паре
            num_cell = row.find("td", id="num")
            time_cell = row.find("td", id="time")

            if num_cell and time_cell:
                # Новая пара
                current_rowspan_left = 0
                current_rowspan = None

                # Получаем номер и время
                number_text = num_cell.get_text(strip=True)
                num_match = re.search(r'(\d+)', number_text)
                number = int(num_match.group(1)) if num_match else 0
                time = time_cell.get_text(strip=True)

                # Проверяем наличие rowspan для будущей обработки
                rowspan_num = num_cell.get('rowspan')
                if rowspan_num:
                    current_rowspan = {
                        'number': number,
                        'time': time,
                        'rows': int(rowspan_num)
                    }
                    current_rowspan_left = current_rowspan['rows'] - 1
            else:
                # Это может быть строка, относящаяся к предыдущей паре через rowspan
                if current_rowspan and current_rowspan_left > 0:
                    number = current_rowspan['number']
                    time = current_rowspan['time']
                    current_rowspan_left -= 1
                else:
                    # Если это не rowspan и нет номера и времени, пропускаем
                    continue

            # Извлекаем информацию о паре
            type_cell = row.find("td", id="lesson")
            name_cell = row.select_one("td[id='lesson'][style='border-left:none;']")
            teacher_cell = row.find("td", id="teacher")
            auditory_cell = row.find("td", id="aud")

            if not all([type_cell, name_cell, teacher_cell, auditory_cell]):
                continue

            # Получаем тип пары
            lesson_type = type_cell.get_text(strip=True)
            if "лек" in lesson_type:
                lesson_type = "Лекция"
            elif "пр.з" in lesson_type:
                lesson_type = "Практика"
            elif "лаб" in lesson_type:
                lesson_type = "Лабораторная"
            else:
                lesson_type = lesson_type.capitalize()

            # Получаем название предмета
            name = extract_subject_name(name_cell)

            # Определяем подгруппу
            subgroup = None
            name_text = name_cell.get_text(strip=True)
            subgroup_match = re.search(r'п/г\s*(\d+)', name_text) or re.search(r'(\d+)\s*подгруппа', name_text)
            if subgroup_match:
                subgroup = int(subgroup_match.group(1))

            # Получаем преподавателя
            teacher_text = teacher_cell.get_text(strip=True)
            teacher = re.sub(r'^преп\.', '', teacher_text).strip()

            # Получаем аудиторию и информацию об онлайн
            auditory = auditory_cell.get_text(strip=True)
            online = "Для студентов с возможностью подключиться он-лайн" in auditory

            # Создаем запись о паре
            lesson = {
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

            # Добавляем пару в список на текущий день
            day_lessons[current_day].append(lesson)

        # Обрабатываем последний день
        if current_day and day_lessons.get(current_day):
            schedule[current_day] = process_day_lessons(day_lessons[current_day])

        result["schedule"] = schedule
        return result
    def extract_subject_name(name_cell):
        """
        Извлекает название предмета из ячейки, игнорируя теги <small>
        и другие служебные элементы
        """
        # Если в ячейке только один тег <a> и нет текста вокруг,
        # используем его содержимое как название предмета
        if len(name_cell.contents) == 1 and name_cell.a:
            return name_cell.a.get_text(strip=True)

        # Если структура сложнее, извлекаем основной текст
        main_text = ""
        for content in name_cell.contents:
            # Пропускаем теги small, где обычно указаны ЭУМКД и другая доп. информация
            if isinstance(content, NavigableString):
                main_text += content.strip()
            elif content.name != 'small':
                main_text += content.get_text(strip=True)

        # Удаляем скобки с содержимым, которые обычно содержат информацию о ЭУМКД
        main_text = re.sub(r'\(.*?\)', '', main_text)
        main_text = main_text.strip()

        # Если после всех обработок текста нет, ищем первый тег <a>
        if not main_text and name_cell.a:
            return name_cell.a.get_text(strip=True)

        return main_text
    def process_day_lessons(lessons):
        """
        Группирует подгруппы одного и того же предмета в одну запись,
        но только если они идут в одно время и имеют тот же тип занятия
        """
        result = []

        # Группируем занятия по ключу - комбинации номера, времени, названия и типа
        grouped = {}
        for lesson in lessons:
            key = lesson["key"]
            if "subgroup" not in lesson:
                # Если это не подгруппа, добавляем как есть
                result.append({k: v for k, v in lesson.items() if k != "key"})
            else:
                # Если это подгруппа, группируем для последующей обработки
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(lesson)

        # Обрабатываем сгруппированные подгруппы
        for key, group_lessons in grouped.items():
            if len(group_lessons) == 1:
                # Если только одна подгруппа, добавляем как есть
                result.append({k: v for k, v in group_lessons[0].items() if k != "key"})
            else:
                # Если несколько подгрупп, создаем иерархию
                # Сортируем по номеру подгруппы
                group_lessons.sort(key=lambda x: x.get("subgroup", 999))

                # Первая подгруппа становится основной
                main_lesson = {k: v for k, v in group_lessons[0].items() if k != "key"}

                # Добавляем остальные подгруппы как вложенные
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

        # Сортируем результат по номеру пары
        result.sort(key=lambda x: x["number"])
        return result

    return parse_schedule(raw, user_login="shizamuru-dev", timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))