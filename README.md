# 🐍 Medusa Backend + Dashboard

> Your smart assistant for BSU schedule with web interface. No more boring tables!

[![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)

[🇷🇺 Russian version](README_RUS.md)

## 🎯 What is this?

FastAPI backend + Next.js dashboard for getting BSU schedule with automatic updates and convenient web interface. All in one Docker container!

## ✨ Features

- 🚀 **Fast API** powered by FastAPI  
- 🎨 **Web interface** built with Next.js and Tailwind CSS
- 🤖 **Auto-updates** schedule in background
- 📊 **Smart weeks** (current/next/previous)
- 🏫 **Group-based** - each group has its own schedule
- 💾 **SQLAlchemy + SQLite** - modern ORM and reliable database
- 🐳 **Docker** - everything in one container, ready image on GHCR
- 🔒 **Security** - multi-stage build, non-root user
- 📁 **Persistent data** - volume for database

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/shizamuru-dev/medusa-backend
cd medusa-backend

# Run ready image
docker-compose up
```

Done! 
- **API** available at http://localhost:8080 📡
- **Dashboard** available at http://localhost:3000 🎨

## 📡 API Endpoints

### 🗓️ Weeks
```
GET /weeks?action=this_week    # Current week
GET /weeks?action=next_week    # Next week  
GET /weeks?action=last_week    # Previous week
```

### 📚 Schedule
```
GET /groups/90002495/schedules/current           # Current group schedule
GET /groups/90002495/schedules?week=15          # Schedule for 15th week
```

## 🛠️ Development

### Without Docker
```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Run
python main.py
```

### With Docker (recommended)
```bash
# For development (local build)
docker-compose -f docker-compose.dev.yml up --build

# For production (ready image)
docker-compose up
```

## 🧪 Testing

```bash
# Tests
pytest

# With coverage and details
pytest --cov=. --cov-report=html --cov-report=xml --verbose

# Code quality
black --check .
isort --check-only .
bandit -r . -x tests/
```

## 📁 Structure

```
medusa-backend/
├── 🐳 Dockerfile              # Multi-stage Docker config (backend + dashboard)
├── 🔧 docker-compose.yml      # Production setup
├── ⚙️ pyproject.toml          # Project and tools configuration
├── 📦 requirements.txt        # Python dependencies
├── 🧪 tests/                  # Tests with pytest
├── 🐍 main.py                 # FastAPI entry point
├── 📁 data/                   # Database data (volume)
├── 🎨 dashboard/              # Next.js web interface
│   ├── app/                   # Next.js App Router
│   ├── components/            # React components
│   ├── lib/                   # API client and utilities
│   ├── package.json           # Node.js dependencies
│   └── next.config.mjs        # Next.js configuration
├── 📚 api/                    # API modules
├── 📚 database/               # Database work (SQLAlchemy)
├── 📚 models/                 # SQLAlchemy models
├── 📚 routes/                 # API routes
├── 📚 tasks/                  # Background tasks
├── 📚 utils/                  # Utilities
├── 📚 hash_utils/             # Hash utilities
└── 📚 logger/                 # Logging
```

## 🛡️ Configuration

### Ports and Network
- **API port**: 8080 (FastAPI backend)
- **Dashboard port**: 3000 (Next.js frontend)
- **Host**: 0.0.0.0 (external access)

### Database
- **Type**: SQLite with SQLAlchemy ORM
- **Location**: `/app/data/Schedules.db` (inside container)
- **Volume**: `medusa_data` for persistent storage

### Security
- Non-root user (UID:GID 1000:1000)
- Multi-stage Docker build
- Health checks every 30 seconds

> **Note**: For development, you can create a `.env` file with additional settings.

## 🚀 Deployment

### Local
```bash
# Ready image (recommended)
docker-compose up

# Or with local build for development
git clone https://github.com/shizamuru-dev/medusa-backend
cd medusa-backend
docker-compose up --build
```

### On Server
```bash
# Create docker-compose.yml with ready image
wget https://raw.githubusercontent.com/shizamuru-dev/medusa-backend/master/docker-compose.yml
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs medusa-backend
```

**Ready image:** `ghcr.io/shizamuru-dev/medusa-backend:latest`

### Monitoring
- **API documentation**: http://localhost:8080/docs
- **Health check**: http://localhost:8080/docs (automatically every 30s)
- **Dashboard interface**: http://localhost:3000
- **Logs**: `docker-compose logs -f medusa`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make commits with ❤️
4. Submit a merge request

## 📜 License

MIT - do whatever you want! 🎉

---

**Made with ❤️ for BelSU students**