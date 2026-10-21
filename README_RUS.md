# 🐍 Medusa Backend

> **Твой умный API помощник для расписания БГУ.**  
> Быстрый, надежный и простой в использовании.

[![Python](https://img.shields.io/badge/python-v3.12+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg?style=flat-square)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)

[🇬🇧 English version](README.md)

---

## 🎯 Обзор

**Medusa Backend** — это высокопроизводительный REST API на **FastAPI**, созданный для получения, парсинга и выдачи расписания занятий **Белгородского государственного университета (НИУ "БелГУ")**.

Он берет на себя всю сложность парсинга университетского расписания, сохраняет его в локальной базе данных для быстрого доступа и поддерживает актуальность с помощью фоновых задач. Идеально подходит для создания собственных приложений, ботов или интеграций с расписанием.

## Кеширование

Расписания и номера учебных недель кешируются в Redis на 45 минут. В Docker Compose
Redis запускается автоматически. Для подключения к внешнему Redis задайте:

```env
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=2700
```

При временной недоступности Redis приложение продолжает работать, обращаясь к
внешнему источнику напрямую.

## ✨ Ключевые особенности

- 🚀 **Высокая производительность**: Работает на **FastAPI** для молниеносных ответов.
- 🤖 **Автообновления**: Фоновые задачи автоматически синхронизируют расписание.
- 📊 **Умные недели**: Интеллектуальная обработка текущей, следующей и предыдущей учебных недель.
- 🏫 **Ориентированность на группы**: Отдельное управление расписанием для каждой студенческой группы.
- 💾 **Надежное хранение**: Использует **SQLAlchemy** + **SQLite** для надежного сохранения данных.
- 🐳 **Готов к Docker**: Готовая к продакшену контейнеризация с multi-stage сборкой.
- 🔒 **Безопасность**: Запускается от имени non-root пользователя для повышенной безопасности.

## 🚀 Быстрый старт

### С использованием Docker (Рекомендуется)

Самый простой способ запустить Medusa Backend — использовать Docker Compose.

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/shizamuru-dev/medusa-backend
cd medusa-backend

# 2. Запустите сервис
docker-compose up -d
```

Готово! API теперь доступно по адресу **http://localhost:8080**.

### Ручная установка

Если вы предпочитаете запускать локально без Docker:

```bash
# 1. Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Установите зависимости
pip install .

# 3. Запустите сервер
python main.py
```

## 📡 Документация API

Medusa Backend предоставляет интерактивную документацию API "из коробки".

- **Swagger UI**: [http://localhost:8080/docs](http://localhost:8080/docs) - Исследуйте и тестируйте эндпоинты интерактивно.
- **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc) - Альтернативный вид документации.

### Основные эндпоинты

| Метод | Эндпоинт | Описание |
| :--- | :--- | :--- |
| `GET` | `/weeks?action=this_week` | Получить информацию о текущей учебной неделе |
| `GET` | `/groups/{id}/schedules/current` | Получить текущее расписание группы |
| `GET` | `/groups/{id}/schedules?week=15` | Получить расписание на конкретную неделю |

## 🛠️ Разработка

### Структура проекта

```
medusa-backend/
├── 🐳 Dockerfile           # Конфиг Docker образа для продакшена
├── 🔧 docker-compose.yml   # Настройка Docker Compose
├── 🐍 main.py              # Точка входа приложения
├── 📚 api/                 # Логика API и сервисы
├── 📚 routes/              # Определения маршрутов API
├── 📚 models/              # Модели базы данных
├── 📚 database/            # Подключение к БД и сессии
├── 📚 tasks/               # Фоновые задачи обновления
├── 📚 utils/               # Вспомогательные утилиты
└── 🧪 tests/               # Набор тестов Pytest
```

### Ключевые функции и методы

Основная логика разбита на небольшие функции, которые можно переиспользовать
и тестировать независимо:

- `api.fetch_week()` получает номер учебной недели с кешированием и повторными запросами к BSU.
- `api.fetch_schedule()` загружает расписание группы, проверяет код недели и кеширует результат.
- `api.parse_schedule()` преобразует HTML расписания в структуру `metadata` и `schedule`, включая обработку `rowspan` и подгрупп.
- `api.process_day_lessons()` объединяет подгруппы одного занятия.
- `utils.week_validator()` проверяет формат и даты кода учебной недели.
- `database.save_schedule()` сохраняет снимок расписания в SQLite.
- `cache.ScheduleCache` предоставляет кеш расписаний, ограничитель запросов и распределённую блокировку Redis.
- `tasks.schedule_update_task()` запускает периодическое обновление, а `tasks.check_schedule_update()` обновляет устаревшие данные.

У функций и методов исходного кода есть docstring с назначением, аргументами,
результатом и исключениями, где это применимо.

### Мониторинг Prometheus и Grafana

Метрики экспортируются приложением через `GET /metrics`. Для запуска отдельного
стека мониторинга выполните:

```bash
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.monitoring.yml up -d
```

После запуска:

- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000> (`admin` / `admin` по умолчанию)

Файл `observability/prometheus.yml` настроен на backend, запущенный на хосте
по адресу `host.docker.internal:8080`. Если backend работает в Compose-сети,
замените target на `medusa:8080` и подключите monitoring Compose к сети
`medusa-network`.

### Запуск тестов

Убедитесь, что ваш код работает корректно с помощью полного набора тестов.

```bash
# Запустить все тесты
pytest

# Запустить с отчетом о покрытии
pytest --cov=. --cov-report=html
```

## 🛡️ Конфигурация

Приложение настроено для работы "из коробки", но вы можете настроить его:

- **Порт**: По умолчанию `8080`. Установите переменную окружения `PORT` для изменения.
- **База данных**: Данные хранятся в `/app/data/Schedules.db` (Docker volume `medusa_data`).
- **Интервал обновлений**: Обновления расписания запускаются автоматически в фоне.

## 🤝 Как помочь

Мы рады вашему вкладу! Не стесняйтесь отправлять Pull Request.

1. Форкните проект
2. Создайте ветку для вашей фичи (`git checkout -b feature/AmazingFeature`)
3. Закоммитьте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📜 Лицензия

Распространяется под лицензией MIT. Смотрите файл `LICENSE` для получения дополнительной информации.

---

<div align="center">
  <sub>Сделано с ❤️ для студентов БелГУ</sub>
</div>
