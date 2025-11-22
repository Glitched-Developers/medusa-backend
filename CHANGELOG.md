# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Removed Next.js dashboard to focus on Backend API functionality.
- Updated project structure and cleaned up unused files.
- Refactored tests for better stability and coverage.
- Updated `.gitignore` configuration.

### Fixed
- Fixed various test failures (2025-11-22).
- Fixed statistics calculation issues (2025-09-12).

## [1.0.0] - 2025-09-15

### Added
- Initial release of Medusa Backend.
- FastAPI implementation for BSU schedule.
- Docker support with multi-stage builds.
- SQLite database integration with SQLAlchemy.
- Background tasks for schedule updates.
- Basic API endpoints for weeks and schedules.
