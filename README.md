# CodeReviewAI

An industry-style AI-powered automated code review platform for Python teams. It analyzes pasted code or uploaded files, detects maintainability and quality issues, scores the codebase, stores review history, and exports reports.

## Features

- FastAPI backend with JWT authentication
- SQLite persistence with SQLAlchemy
- AST-based Python code analyzer
- Optional integration points for `pylint`, `flake8`, `radon`, and OpenAI
- Quality, maintainability, readability, and complexity scoring
- Line-level issue metadata for frontend highlighting
- JSON and PDF report export
- Previous scan history per user
- Modern dark SaaS dashboard
- Drag and drop upload, code editor, analytics charts, AI explanation panel
- Multi-language analyzer architecture
- GitHub repository and pull request review simulation endpoints
- Rate limiting middleware
- Docker and GitHub Actions CI scaffold
- Unit tests and sample code fixtures

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Demo Login

Register a user from the UI, then sign in. Scans are stored against your account.

## Environment

Create a `.env` file if you want to override defaults:

```env
DATABASE_URL=sqlite:///./codereviewai.db
SECRET_KEY=change-me
OPENAI_API_KEY=
```

If `OPENAI_API_KEY` is not provided, the app uses a deterministic local suggestion engine.

## Architecture

```text
api/          FastAPI app, routes, middleware
analyzers/    Language analyzer interfaces and Python AST implementation
auth/         Password hashing and JWT helpers
database/     SQLAlchemy session and initialization
frontend/     HTML/CSS/JS dashboard
models/       ORM models and Pydantic schemas
reports/      JSON/PDF report generation
services/     Review orchestration, AI suggestions, scoring, GitHub simulation
utils/        Configuration and shared helpers
tests/        Unit tests and fixtures
```

## Running Tests

```bash
pytest
```

## Docker

```bash
docker build -t codereviewai .
docker run -p 8000:8000 codereviewai
```

## Deployment

The project includes:

- `Dockerfile` for container hosting
- `Procfile` for Heroku-style platforms
- `render.yaml` for Render blueprint deployments

For Render, create a new Blueprint from the GitHub repository after pushing this code. Render will run:

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

## Notes

This project is designed as a resume-worthy SaaS prototype. The analyzer is production-structured and extensible, while external tools such as `pylint`, `flake8`, and `radon` are wrapped so the app degrades gracefully when those tools are unavailable.
