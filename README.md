# Social Media API

A small **FastAPI** social-media backend (posts and comments) built while following
the **Mastering REST APIs** course from **Packt** on **Coursera**.

This is a learning project that walks through building a production-style REST API:
async request handling, a SQLite database, environment-based configuration,
structured logging, and a test suite.

## Features

- **Posts & comments** REST endpoints backed by SQLite (via `databases` + SQLAlchemy Core)
- **Environment-based config** (`dev` / `test` / `prod`) using `pydantic-settings`
- **Structured logging** with `rich` console output and rotating JSON file logs
- **Request correlation IDs** via `asgi-correlation-id`
- **Email obfuscation** log filter to keep PII out of logs
- **Tests** with `pytest` + `httpx` against an isolated, auto-rolled-back test database

## Tech stack

| Concern        | Library |
|----------------|---------|
| Web framework  | FastAPI |
| ASGI server    | Uvicorn (standard) |
| Database       | `databases[aiosqlite]` + SQLAlchemy Core |
| Config         | pydantic-settings, python-dotenv |
| Logging        | rich, python-json-logger, asgi-correlation-id, logtail-python |
| Testing        | pytest, httpx |
| Linting        | ruff |

## Project structure

```
social_media_api/
├── main.py            # FastAPI app, lifespan, exception logging
├── config.py          # Dev/Test/Prod settings (env-prefixed)
├── database.py        # Table definitions + database connection
├── logging_conf.py    # dictConfig: formatters, filters, handlers
├── models/
│   └── post.py        # Pydantic request/response models
├── routers/
│   └── post.py        # /posts and /comments endpoints
└── tests/             # pytest suite
```

## Getting started

This project uses [uv](https://docs.astral.sh/uv/) (an `uv.lock` is committed).

```bash
# Install dependencies
uv sync

# or, with pip:
pip install -r requirements.txt -r requirements-dev.txt
```

### Configuration

Copy the example env file and fill in values:

```bash
cp .env.example .env
```

| Variable          | Description |
|-------------------|-------------|
| `ENV_STATE`       | `dev`, `test`, or `prod` (defaults to dev) |
| `DATABASE_URL`    | SQLite URL, e.g. `sqlite:///data.db` |
| `LOGTAIL_API_KEY` | Optional — token for shipping logs to Logtail |

Settings are read per environment using prefixes — e.g. `DEV_DATABASE_URL`,
`PROD_DATABASE_URL`. The active environment is selected by `ENV_STATE`.

### Run the app

```bash
uv run uvicorn social_media_api.main:app --reload
```

Then open the interactive docs at <http://127.0.0.1:8000/docs>.

## API endpoints

| Method | Path                        | Description |
|--------|-----------------------------|-------------|
| POST   | `/posts`                    | Create a post |
| GET    | `/posts`                    | List all posts |
| POST   | `/comments`                 | Add a comment to a post |
| GET    | `/posts/{post_id}/comments` | List comments for a post |
| GET    | `/posts/{post_id}`          | Get a post with its comments |

## Activate the environment
```bash
source .venv/bin/activate
```

## Running tests

```bash
uv run pytest
```

Tests run against the `test` environment, which uses a separate `test.db` with
`DB_FORCE_ROLL_BACK=True` so every connection's changes are rolled back —
each test starts from a clean database.

## Logging

Logging is configured in `logging_conf.py` and initialized on app startup:

- **Console** — human-readable output via `rich`, with correlation IDs.
- **File** — rotating JSON logs (`social_media_api.log`) suitable for log aggregation.
- **Email obfuscation** — a logging filter masks email addresses passed via
  `extra={"email": ...}` before they're written.

---

*Built for educational purposes as part of Packt's "Mastering REST APIs" course on Coursera.*
