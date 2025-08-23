# 🐍 Medusa Backend

> Твой умный помощник для расписания БГУ. Больше никаких скучных таблиц!

[![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitLab-orange.svg)](https://gitlab.com)

## 🎯 Что это?

FastAPI бэкенд для получения расписания БГУ с автоматическими обновлениями и удобным API. Просто, быстро, работает!

## ✨ Фишки

- 🚀 **Быстрый API** на FastAPI
- 🤖 **Автообновления** расписания в фоне
- 📊 **Умные недели** (текущая/следующая/предыдущая)
- 🏫 **По группам** - каждой группе свое расписание
- 💾 **SQLite** - простая база данных
- 🐳 **Docker** - запуск одной командой
- ⚡ **CI/CD** - автосборка и тесты

## 🚀 Быстрый старт

```bash
# Клонируем
git clone <your-repo>
cd medusa-backend

# Настраиваем
cp .env.example .env

# Запускаем
docker-compose up --build
```

Готово! API доступно на http://localhost:8000 🎉

## 📡 API Endpoints

### 🗓️ Недели
```
GET /weeks?action=this_week    # Текущая неделя
GET /weeks?action=next_week    # Следующая неделя  
GET /weeks?action=last_week    # Прошлая неделя
```

### 📚 Расписание
```
GET /groups/ПИ-20/schedules/current           # Текущее расписание группы
GET /groups/ПИ-20/schedules?week=15          # Расписание на 15-ю неделю
```

## 🛠️ Разработка

### Без Docker
```bash
# Виртуальная среда
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Зависимости
pip install -r requirements.txt

# Запуск
python main.py
```

### С Docker (рекомендуется)
```bash
docker-compose up --build
```

## 🧪 Тестирование

```bash
# Тесты
pytest

# С покрытием
pytest --cov=. --cov-report=html

# Качество кода
black --check .
flake8 .
```

## 🏗️ CI/CD

Автоматическая сборка и деплой! Настройка в `CI-CD-SETUP.md`

**Что происходит при пуше:**
1. ✅ Тесты
2. ✅ Проверка качества кода
3. ✅ Сборка Docker образа
4. ✅ Загрузка на ghcr.io

## 📁 Структура

```
medusa-backend/
├── 🐳 Dockerfile              # Docker конфиг
├── 🔧 docker-compose.yml      # Локальный запуск
├── ⚙️  .gitlab-ci.yml         # CI/CD pipeline
├── 📦 requirements.txt        # Python зависимости
├── 🧪 tests/                  # Тесты
├── 🐍 main.py                 # Точка входа
└── 📚 [modules]/              # Модули приложения
```

## 🛡️ Переменные окружения

Копируй `.env.example` → `.env` и настраивай:

```env
PORT=8000                                    # Порт сервера
DATABASE_URL=sqlite:///./Schedules.db        # База данных
BSU_API_URL=https://bsu-api-endpoint.com     # API БГУ
UPDATE_INTERVAL_HOURS=6                      # Интервал обновлений
```

## 🚀 Деплой

### Локально
```bash
docker-compose up
```

### На сервере
```bash
# Используем готовый образ с ghcr.io
# Раскомментируй image в docker-compose.yml
docker-compose up
```

## 🤝 Как помочь

1. Форкни репозиторий
2. Создай ветку для фичи
3. Делай коммиты с ❤️
4. Отправляй merge request

## 📜 Лицензия

MIT - делай что хочешь! 🎉

---

**Сделано с ❤️ для студентов БГУ**