# 🐍 Medusa Backend

> Твой умный помощник для расписания БГУ. Больше никаких скучных таблиц!

[![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)

## 🎯 Что это?

FastAPI бэкенд для получения расписания БГУ с автоматическими обновлениями и удобным API. Работает на порту 8080 с готовым Docker образом!

## ✨ Фишки

- 🚀 **Быстрый API** на FastAPI
- 🤖 **Автообновления** расписания в фоне
- 📊 **Умные недели** (текущая/следующая/предыдущая)
- 🏫 **По группам** - каждой группе свое расписание
- 💾 **SQLAlchemy + SQLite** - современная ORM и надежная база
- 🐳 **Docker** - готовый образ на GHCR
- 🔒 **Безопасность** - multi-stage сборка, non-root пользователь
- 📁 **Постоянные данные** - volume для базы данных

## 🚀 Быстрый старт

```bash
# Клонируем
git clone https://github.com/shizamuru-dev/medusa-backend
cd medusa-backend

# Запускаем готовый образ
docker-compose up
```

Готово! API доступно на http://localhost:8080 🎉

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
# Для разработки (локальная сборка)
docker-compose -f docker-compose.dev.yml up --build

# Для продакшена (готовый образ)
docker-compose up
```

## 🧪 Тестирование

```bash
# Тесты
pytest

# С покрытием и подробностями
pytest --cov=. --cov-report=html --cov-report=xml --verbose

# Качество кода
black --check .
isort --check-only .
bandit -r . -x tests/
```

## 🏗️ CI/CD

Автоматическая сборка и деплой через GitHub Actions!

**Что происходит при пуше:**
1. ✅ Тесты и линтеры (pytest, black, isort)
2. ✅ Проверка безопасности (bandit)
3. ✅ Сборка multi-stage Docker образа
4. ✅ Загрузка на GitHub Container Registry (ghcr.io)

## 📁 Структура

```
medusa-backend/
├── 🐳 Dockerfile              # Multi-stage Docker конфиг
├── 🔧 docker-compose.yml      # Продакшен запуск
├── ⚙️  pyproject.toml          # Конфигурация проекта и инструментов
├── 📦 requirements.txt        # Python зависимости
├── 🧪 tests/                  # Тесты с pytest
├── 🐍 main.py                 # Точка входа FastAPI
├── 📁 data/                   # Данные базы (volume)
├── 📚 api/                    # API модули
├── 📚 database/               # Работа с БД (SQLAlchemy)
├── 📚 models/                 # SQLAlchemy модели
├── 📚 routes/                 # API маршруты
├── 📚 tasks/                  # Фоновые задачи
├── 📚 utils/                  # Утилиты
├── 📚 hash_utils/             # Работа с хешами
└── 📚 logger/                 # Логирование
```

## 🛡️ Конфигурация

### Порт и сеть
- **Порт**: 8080 (фиксированно в коде)
- **Хост**: 0.0.0.0 (доступ снаружи)

### База данных
- **Тип**: SQLite с SQLAlchemy ORM
- **Расположение**: `/app/data/Schedules.db` (внутри контейнера)
- **Volume**: `medusa_data` для постоянного хранения

### Безопасность
- Non-root пользователь (UID:GID 1000:1000)
- Multi-stage Docker сборка
- Health checks каждые 30 секунд

> **Примечание**: Для разработки можно создать `.env` файл с дополнительными настройками.

## 🚀 Деплой

### Локально
```bash
# Готовый образ (рекомендуется)
docker-compose up

# Или с локальной сборкой для разработки
git clone https://github.com/shizamuru-dev/medusa-backend
cd medusa-backend
docker-compose up --build
```

### На сервере
```bash
# Создаем docker-compose.yml с готовым образом
wget https://raw.githubusercontent.com/shizamuru-dev/medusa-backend/master/docker-compose.yml
docker-compose up -d

# Проверяем состояние
docker-compose ps
docker-compose logs medusa-backend
```

**Готовый образ:** `ghcr.io/shizamuru-dev/medusa-backend:latest`

### Мониторинг
- **API документация**: http://localhost:8080/docs
- **Health check**: http://localhost:8080/docs (автоматически каждые 30с)
- **Логи**: `docker-compose logs -f medusa-backend`

## 🤝 Как помочь

1. Форкни репозиторий
2. Создай ветку для фичи
3. Делай коммиты с ❤️
4. Отправляй merge request

## 📜 Лицензия

MIT - делай что хочешь! 🎉

---

**Сделано с ❤️ для студентов БГУ**