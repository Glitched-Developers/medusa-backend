# 🐍 Medusa Backend

> **Your smart API assistant for BSU schedule.**  
> Fast, reliable, and easy to use.

[![Python](https://img.shields.io/badge/python-v3.12+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg?style=flat-square)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)

[🇷🇺 Russian version](README_RUS.md)

---

## 🎯 Overview

**Medusa Backend** is a high-performance REST API built with **FastAPI** designed to fetch, parse, and serve class schedules for **Belgorod State University (BSU)**. 

It handles the complexity of parsing the university's schedule, stores it in a local database for quick access, and keeps it up-to-date with background tasks. Perfect for building your own schedule apps, bots, or integrations.

## Caching

Schedules and academic week numbers are cached in Redis for 45 minutes. Docker
Compose starts Redis automatically. Configure an external Redis instance with:

```env
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=2700
```

If Redis is temporarily unavailable, the application falls back to the upstream
source and continues serving requests.

## ✨ Key Features

- 🚀 **High Performance**: Powered by **FastAPI** for lightning-fast responses.
- 🤖 **Auto-Updates**: Background tasks automatically keep the schedule in sync.
- 📊 **Smart Weeks**: Intelligent handling of current, next, and previous academic weeks.
- 🏫 **Group-Centric**: Dedicated schedule management for each student group.
- 💾 **Reliable Storage**: Uses **SQLAlchemy** + **SQLite** for robust data persistence.
- 🐳 **Docker Ready**: Production-ready containerization with multi-stage builds.
- 🔒 **Secure**: Runs as a non-root user for enhanced security.

## 🚀 Quick Start

### Using Docker (Recommended)

The easiest way to run Medusa Backend is with Docker Compose.

```bash
# 1. Clone the repository
git clone https://github.com/shizamuru-dev/medusa-backend
cd medusa-backend

# 2. Start the service
docker-compose up -d
```

That's it! The API is now running at **http://localhost:8080**.

### Manual Installation

If you prefer running it locally without Docker:

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install .

# 3. Run the server
python main.py
```

## 📡 API Documentation

Medusa Backend provides interactive API documentation out of the box.

- **Swagger UI**: [http://localhost:8080/docs](http://localhost:8080/docs) - Explore and test endpoints interactively.
- **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc) - Alternative documentation view.

### Common Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/weeks?action=this_week` | Get current academic week info |
| `GET` | `/groups/{id}/schedules/current` | Get current schedule for a group |
| `GET` | `/groups/{id}/schedules?week=15` | Get schedule for a specific week |
| `GET` | `/stats` | Get system statistics |

## 🛠️ Development

### Project Structure

```
medusa-backend/
├── 🐳 Dockerfile           # Production Docker image config
├── 🔧 docker-compose.yml   # Docker Compose setup
├── 🐍 main.py              # Application entry point
├── 📚 api/                 # API logic and services
├── 📚 routes/              # API route definitions
├── 📚 models/              # Database models
├── 📚 database/            # Database connection & session
├── 📚 tasks/               # Background update tasks
├── 📚 utils/               # Helper utilities
└── 🧪 tests/               # Pytest suite
```

### Running Tests

Ensure your code is working correctly with the comprehensive test suite.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html
```

## 🛡️ Configuration

The application is configured to run out of the box, but you can customize it:

- **Port**: Defaults to `8080`. Set `PORT` env var to change.
- **Database**: Data is stored in `/app/data/Schedules.db` (Docker volume `medusa_data`).
- **Update Interval**: Schedule updates run automatically in the background.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <sub>Made with ❤️ for BSU students</sub>
</div>
