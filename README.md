# FastAPI + SvelteKit Full-Stack Application

A modern full-stack web application combining FastAPI (Python) backend with SvelteKit (TypeScript) frontend.

## 🏗️ Project Structure

```
fastapi-svelte/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   │   ├── routers/ # API routes
│   │   ├── models.py
│   │   ├── config.py
│   │   └── ...
│   ├── tests/       # Backend tests
│   └── pyproject.toml
├── frontend/        # SvelteKit frontend
│   ├── src/
│   │   ├── lib/     # Shared components & utilities
│   │   ├── routes/  # SvelteKit routes
│   │   └── ...
│   └── package.json
└── docker-compose.yml
```

## 🚀 Features

### Backend (FastAPI)

- **Authentication & Authorization**: JWT-based auth with refresh tokens
- **Role-Based Access Control**: Flexible permission system with scopes
- **Database**: PostgreSQL with SQLModel ORM
- **Migrations**: Alembic for database migrations
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Image Upload**: Cloudinary integration for recipe images
- **Real-time Updates**: SSE (Server-Sent Events) for game sessions

### Frontend (SvelteKit)

- **Modern UI**: Tailwind CSS with dark mode support
- **Type Safety**: Full TypeScript support with auto-generated API types
- **Forms**: Sveltekit-superforms with Zod validation
- **Rich Text Editor**: Tiptap for recipe instructions
- **Components**: shadcn-svelte UI components
- **Authentication**: JWT token management with HTTP-only cookies

## 📋 Prerequisites

- **uv** (Python package manager) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Bun 1.1+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

## 🛠️ Setup

### Backend Setup

1. **Navigate to backend directory**

    ```bash
    cd backend
    ```

2. **Install dependencies with uv**

    ```bash
    uv sync
    ```

    This will automatically create a virtual environment and install all dependencies.

3. **Configure environment**
   Create `.env` in the repository root (one level above `backend/`):

    ```env
    PROJECT_NAME=FastAPI-Svelte
    ENVIRONMENT=local
    FRONTEND_HOST=http://localhost:5173

    # Database
    POSTGRES_SERVER=localhost
    POSTGRES_PORT=5432
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=your_password
    POSTGRES_DB=fastapi_db

    # Security
    SECRET_KEY=your_secret_key_here
    FIRST_SUPERUSER=admin@example.com
    FIRST_SUPERUSER_PASSWORD=admin_password

    # Cloudinary (for image uploads)
    CLOUDINARY_CLOUD_NAME=your_cloud_name
    CLOUDINARY_API_KEY=your_api_key
    CLOUDINARY_API_SECRET=your_api_secret
    ```

4. **Run database migrations**

    Make sure you have either a local PostgreSQL instance running or a Docker container with the database service up (see Docker section below). Then run:

    ```bash
    uv run alembic upgrade head
    ```

5. **Start backend server**

    ```bash
    uv run uvicorn app.main:app --reload
    ```

    Backend will be available at `http://localhost:8000`
    - API docs: `http://localhost:8000/docs`
    - Alternative docs: `http://localhost:8000/redoc`

### Frontend Setup

1. **Navigate to frontend directory**

    ```bash
    cd frontend
    ```

2. **Install dependencies**

    ```bash
    bun install
    ```

3. **Generate API types after backend contract changes**

    Run the repository script from the project root so it first refreshes the OpenAPI document:

    ```bash
    cd ..
    ./scripts/generate-client.sh
    cd frontend
    ```

4. **Start development server**

    ```bash
    bun run dev
    ```

    Frontend will be available at `http://localhost:5173`

## 📊 Observability and visitor metrics

Traffic analytics are first-party and appear directly on the administration dashboard. SvelteKit
records two counters:

- `site.page_view`: the initial page and each completed SvelteKit navigation, grouped by route
  template. Concrete slugs, IDs, and query strings are not metric attributes.
- `site.browser_session.started`: once per browser tab's `sessionStorage` lifetime. This is a
  per-tab session count, not an exact count of unique people or browsers, and it does not use a
  persistent visitor ID.

The SvelteKit server validates each batch, determines whether the request is authenticated, and
forwards it to the backend using a private server-to-server token. The backend increments
non-identifying hourly aggregates in PostgreSQL; the analytics table does not store raw events,
concrete URLs, IP addresses, user IDs, or persistent visitor identifiers. Aggregate buckets older
than 90 days are deleted during ingestion. The summary endpoint is restricted to superusers.

Shallow-routing entries used by dialogs, sheets, and sidebars do not count as page views. Browser
analytics are disabled when Do Not Track or Global Privacy Control is enabled. The administration
dashboard renders the seven-day series with D3 and refreshes its aggregate data every 30 seconds
while the tab is visible.

Generate one private ingestion token:

```bash
openssl rand -hex 32
```

Copy the generated value into the backend's root `.env`:

```env
ANALYTICS_INGEST_TOKEN=<generated-value>
```

Put the exact same value in `frontend/.env`:

```env
ANALYTICS_INGEST_TOKEN=<generated-value>
```

The variable has no `PUBLIC_` prefix, so it remains available only to the SvelteKit server. Never
commit either `.env` file or expose this token in browser code.

Sentry remains a separate, optional service for errors and performance traces only. It is not the
source of the visitor counters shown in the admin dashboard. Configure backend Sentry monitoring in
the root `.env`:

```env
SENTRY_DSN=https://your-backend-dsn
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_SEND_DEFAULT_PII=false
```

Configure the frontend runtime with the values documented in `frontend/.env.example`:

```env
PUBLIC_SENTRY_DSN=https://your-frontend-dsn
PUBLIC_SENTRY_ENVIRONMENT=production
PUBLIC_SENTRY_TRACES_SAMPLE_RATE=0.1
```

A Sentry DSN identifies the ingest project and is safe to expose to the browser. Never expose a
Sentry auth token. `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, and `SENTRY_PROJECT` are optional build-only
variables; when all three are present, the production build uploads source maps. The frontend and
backend can use the same Sentry project initially, although separate projects make errors and
performance data easier to filter as the application grows.

`SENTRY_API_TOKEN` is not read by this application and is not needed for the admin analytics
dashboard. Use Sentry itself for error investigation, navigation and backend request traces, and Web
Vitals. Leaving the corresponding DSN empty disables Sentry without disabling first-party traffic
analytics.

## 🐳 Docker Setup

If you want to run the full stack with Docker, use the following sequence to ensure the database is recreated and services are built from the latest images:

```bash
# Stop and remove containers, networks, and volumes created by previous runs
docker compose down -v --remove-orphans

# (Optional) Build images from Dockerfiles
docker compose build

# Start services in detached mode
docker compose up -d
```

Notes:

- `docker compose down -v --remove-orphans` removes containers, associated named volumes, and any orphaned containers from prior compose runs — useful when changing database schema or clearing persisted state.
- `docker compose build` forces rebuild of images when you changed Dockerfile or dependencies.
- `docker compose up -d` starts services in the background.

After the stack is up, you may need to run database migrations inside the backend container (or run them from your host against the DB):

```bash
# Run migrations from the backend container (example)
docker compose exec backend uv run alembic upgrade head
```

This will start the PostgreSQL database, backend API server, and frontend development server as defined in `docker-compose.yml`.

## 🧪 Testing

### Backend Tests

The canonical backend test command, also used by CI, runs pytest and PostgreSQL entirely in
dedicated Docker containers:

```bash
./scripts/test-backend.sh
```

You can pass normal pytest arguments through the script, for example:

```bash
./scripts/test-backend.sh tests/test_recipe_consumption.py -v
```

CI also records backend line coverage and requires at least 70%:

```bash
./scripts/test-backend.sh --cov=app --cov-report=term-missing --cov-fail-under=70
```

The runner builds a dedicated Python 3.13 test image and starts an ephemeral PostgreSQL database in
a uniquely named Compose project. It does not publish database ports, load `.env`, mount the source
tree, or reuse the development database volume. Containers, the internal network, and the in-memory
database are removed automatically after the run.

For local development, pytest can also run directly from `backend/`:

```bash
cd backend
uv run pytest
uv run pytest tests/api/routes/test_users.py -v
```

Host-side pytest, including runs started from the VS Code Testing panel, automatically starts a
dedicated PostgreSQL test container. The database is bound only to a random `127.0.0.1` port,
migrated before collection, and removed after the session. Test-only settings are injected before
the application is imported, so the development `.env`, database, and Docker volume are not used.
Only one database-backed host test session can run per checkout at a time.

Test discovery does not start Docker. A suite consisting only of tests marked `no_db` can also run
without Docker:

```bash
cd backend
uv run pytest -m no_db
```

Docker must be installed and running for database-backed host or Testing panel runs.

### Type Checking

```bash
# Backend
cd backend
uv run uvx ty check

# Frontend
cd frontend
bun run check
```

## 🎨 Code Quality

### Pre-commit Hooks

The backend uses **prek** (installed as a dev dependency) for pre-commit checks:

```bash
cd backend
uv run prek install
```

Frontend uses standard pre-commit hooks:

```bash
pre-commit install
```

This will automatically run on commit:

- **Backend**: Ruff (linting & formatting) via prek
- **Frontend**: Prettier (formatting)
- YAML/JSON validation
- Trailing whitespace removal

### Manual Formatting

```bash
# Backend
cd backend
uv run ruff format .
uv run ruff check --fix .

# Or use prek to run checks manually
uv run prek run

# Frontend
cd frontend
bun run format
```

## 📚 API Documentation

When the backend is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔑 Default Credentials

After initial setup with `FIRST_SUPERUSER`:

- Email: Value of `FIRST_SUPERUSER` env variable
- Password: Value of `FIRST_SUPERUSER_PASSWORD` env variable

## 📦 Main Dependencies

### Backend

- **FastAPI**: Modern web framework
- **SQLModel**: SQL databases with Python type hints
- **Pydantic**: Data validation
- **Alembic**: Database migrations
- **Python-Jose**: JWT tokens
- **Cloudinary**: Image hosting

### Frontend

- **SvelteKit**: Full-stack framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first CSS
- **Tiptap**: Rich text editor
- **Zod**: Schema validation
- **openapi-fetch**: Type-safe API client

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

## Open Food Facts barcode import

Users with the `ingredients:create` permission can scan a packaged-food barcode from
the ingredient administration page. The browser reads the barcode with the phone's
rear camera, while the backend retrieves product and per-100g nutrition data from
Open Food Facts. The values remain editable and must be reviewed before saving.

Set `OPENFOODFACTS_USER_AGENT` in `.env` to identify your deployed app with a URL or
contact address, for example:

```dotenv
OPENFOODFACTS_USER_AGENT="MyRecipeApp/1.0 (https://recipes.example.com)"
```

Camera access requires HTTPS in production (localhost is allowed during local
development). If camera access is unavailable or denied, the scanner also accepts a
barcode typed manually.

## Required and consumed ingredient amounts

Recipe ingredients can optionally specify an amount actually consumed in addition to
the amount required for cooking. Shopping and ingredient lists continue to show the
full required amount, while calories, macros, and calculated recipe weight use the
consumed amount. Leave it blank to treat the full amount as consumed.

For example, a deep-frying recipe can require 1 L of oil but record 0.1 L as consumed,
preventing the unused frying oil from being included in the recipe nutrition totals.
