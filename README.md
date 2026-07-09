# Social Media API

A small **FastAPI** social-media backend (posts and comments) built while following
the **Mastering REST APIs** course from **Packt** on **Coursera**.

This is a learning project that walks through building a production-style REST API:
async request handling, a SQLite database, environment-based configuration,
structured logging, and a test suite.

## Features

- **Posts, comments & likes** REST endpoints backed by SQLite (via `databases` + SQLAlchemy Core)
- **JWT authentication** — register, login, and email confirmation with `python-jose` + `passlib`/bcrypt
- **Background tasks** — send registration/confirmation emails via Mailgun and generate post
  images via the DeepAI API, then patch the post with the resulting `image_url`
- **File uploads** to Backblaze B2 (`/upload`)
- **Environment-based config** (`dev` / `test` / `prod`) using `pydantic-settings`
- **Structured logging** with `rich` console output and rotating JSON file logs
- **Request correlation IDs** via `asgi-correlation-id`
- **Email obfuscation** log filter to keep PII out of logs
- **Tests** with `pytest` + `httpx` against an isolated, auto-rolled-back test database

## Tech stack

| Concern         | Library |
|-----------------|---------|
| Web framework   | FastAPI |
| ASGI server     | Uvicorn (standard) |
| Database        | `databases[aiosqlite]` + SQLAlchemy Core |
| Auth            | python-jose (JWT), passlib[bcrypt], python-multipart |
| Config          | pydantic-settings, python-dotenv |
| Email / images  | httpx (Mailgun, DeepAI) |
| File storage    | b2sdk, aiofiles (Backblaze B2) |
| Logging         | rich, python-json-logger, asgi-correlation-id, logtail-python |
| Testing         | pytest, httpx, pytest-mock, pyfakefs |
| Linting         | ruff |

## Project structure

```
run.py                 # Client script — one function per endpoint (see below)
social_media_api/
├── main.py            # FastAPI app, lifespan, exception logging
├── config.py          # Dev/Test/Prod settings (env-prefixed)
├── database.py        # Table definitions + database connection
├── security.py        # Password hashing, JWT create/verify, current-user dep
├── tasks.py           # Background tasks: Mailgun email + DeepAI image generation
├── logging_conf.py    # dictConfig: formatters, filters, handlers
├── libs/
│   └── b2.py          # Backblaze B2 upload helper
├── models/
│   ├── post.py        # Post / comment / like request/response models
│   └── user.py        # User models
├── routers/
│   ├── post.py        # /posts, /comments, /like endpoints
│   ├── user.py        # /register, /token, /confirm endpoints
│   └── upload.py      # /upload endpoint
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

| Variable              | Description |
|-----------------------|-------------|
| `ENV_STATE`           | `dev`, `test`, or `prod` (defaults to dev) |
| `DATABASE_URL`        | SQLite URL, e.g. `sqlite:///data.db` |
| `DB_FORCE_ROLL_BACK`  | Roll back every connection's changes (used by the test env) |
| `LOGTAIL_API_KEY`     | Optional — token for shipping logs to Logtail |
| `MAILGUN_DOMAIN`      | Mailgun sending domain (registration/confirmation emails) |
| `MAILGUN_API_KEY`     | Mailgun API key |
| `DEEPAI_API_KEY`      | DeepAI key for post image generation |
| `B2_KEY_ID`           | Backblaze B2 key ID (file uploads) |
| `B2_APPLICATION_KEY`  | Backblaze B2 application key |
| `B2_BUCKET_NAME`      | Backblaze B2 bucket name |

Except `ENV_STATE`, settings are read per environment using prefixes — e.g.
`DEV_DATABASE_URL`, `PROD_MAILGUN_API_KEY`. The active environment is selected
by `ENV_STATE`.

### Run the app

```bash
uv run uvicorn social_media_api.main:app --reload
```

Then open the interactive docs at <http://127.0.0.1:8000/docs>.

## API endpoints

| Method | Path                        | Auth | Description |
|--------|-----------------------------|:----:|-------------|
| POST   | `/register`                 |      | Register a user (sends a confirmation email) |
| POST   | `/token`                    |      | Log in, returns a JWT access token |
| GET    | `/confirm/{token}`          |      | Confirm an email from the link's token |
| POST   | `/posts`                    |  ✓   | Create a post (optional `?prompt=` triggers image generation) |
| GET    | `/posts`                    |      | List posts (`?sorting=newest\|oldest\|most_liked`) |
| POST   | `/comments`                 |  ✓   | Add a comment to a post |
| GET    | `/posts/{post_id}/comments` |      | List comments for a post |
| GET    | `/posts/{post_id}`          |      | Get a post with its comments |
| POST   | `/like`                     |  ✓   | Like a post |
| POST   | `/upload`                   |      | Upload a file to Backblaze B2 |

Authenticated endpoints expect an `Authorization: Bearer <token>` header
(obtain the token from `/token`).

## Client script (`run.py`)

[`run.py`](run.py) is a small `httpx` client with one function per endpoint,
handy for exercising a running server without the Swagger UI:

```bash
# start the API in one terminal, then:
python run.py
```

`main()` chains a full flow (register → login → create post → …). Because image
generation runs in a background task, `create_post` returns `image_url: null`
immediately; use `wait_for_image_url(post_id)` to poll `GET /posts/{post_id}`
until the URL is populated.

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
