# AGENTS.md

## Scope

These instructions apply to the entire repository. Prefer the conventions already used in the
nearest file when they are more specific than this guide.

## Project overview

This is a FastAPI and SvelteKit application for recipes, ingredients, and game sessions.

- `backend/`: Python 3.13, FastAPI, SQLModel, PostgreSQL, Alembic, and pytest.
- `frontend/`: Svelte 5, SvelteKit, TypeScript, Tailwind CSS, shadcn-svelte, and Bun.
- `compose.yaml`: PostgreSQL and backend services. The frontend service is currently commented out.
- `.env`: shared local configuration loaded by Compose and the backend. Never commit it or print
  secrets from it.

## Important paths

- `backend/app/main.py`: FastAPI application and router registration.
- `backend/app/models.py`: SQLModel database models and public/create/update schemas.
- `backend/app/routers/`: API endpoints.
- `backend/app/migrations/versions/`: Alembic migrations.
- `backend/tests/`: backend tests.
- `frontend/src/routes/`: SvelteKit pages, layouts, actions, and server endpoints.
- `frontend/src/lib/components/`: application components.
- `frontend/src/lib/components/ui/`: shadcn-svelte UI primitives.
- `frontend/src/lib/schemas/schemas.ts`: client-side form schemas.
- `frontend/src/lib/client/`: generated OpenAPI client. Do not edit these files by hand.
- `frontend/openapi-ts.config.ts`: generated-client configuration.

## Setup and common commands

Run backend commands from `backend/`:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

The canonical backend test runner executes pytest and PostgreSQL entirely in isolated Docker
containers:

```bash
./scripts/test-backend.sh
./scripts/test-backend.sh tests/test_recipe_consumption.py -v
```

Database-backed tests may also run directly from `backend/` or through the VS Code Testing panel:

```bash
cd backend
uv run pytest
uv run pytest tests/test_recipe_consumption.py -v
```

Host-side pytest automatically starts a dedicated test database on a random loopback port, injects
test-only configuration, applies migrations, and removes the database after the session. It must
never load `.env`, reuse the development database volume, or connect to the normal PostgreSQL port.
Use `uv run pytest -m no_db` for a database-free run that does not start Docker.

Run frontend commands from `frontend/`:

```bash
bun install
bun run dev
bun run check
bun run lint
bun run build
bun run test
bun run generate-client
```

For focused work, run the narrowest relevant test first, then the broader checks before handoff.
When changing dependencies, update and commit the corresponding lockfile (`backend/uv.lock` or
`frontend/bun.lock`).

## Backend conventions

- Use type annotations throughout and follow the existing FastAPI dependency-injection patterns.
- Keep database models and API schemas explicit. Do not expose internal fields accidentally.
- Use `Security(...)` and the existing permission scopes for protected endpoints. New mutating
  endpoints normally need an appropriate create, update, or delete scope.
- Raise `HTTPException` with an appropriate status and a useful, non-sensitive message at API
  boundaries.
- External HTTP calls belong in a small service module, not directly in a router. Set timeouts,
  identify the application when required, and translate upstream failures into application-level
  errors.
- Any persistent schema change requires a new Alembic migration. Do not rewrite a migration that
  may already have been applied.
- Mark database-free unit tests with `@pytest.mark.no_db` when appropriate. Add regression tests for
  parsing, validation, permission, and error-handling changes.
- Keep test-only credentials and services in the test Compose files. The fully containerized runner
  must not publish the database port. The host/VS Code override may bind PostgreSQL only to a random
  `127.0.0.1` port. Never load `.env`, reuse the development database volume, mount development
  sources into the test runner, or expose the test database on a LAN-facing interface.

Python formatting is enforced by Ruff with an 88-character line length and spaces for indentation.
Use `uv`; do not introduce pip-managed environment files.

## Frontend conventions

- Use TypeScript and keep strict typing intact. Avoid `any` unless an external boundary genuinely
  requires it and the value is narrowed immediately.
- Follow Svelte 5/SvelteKit routing and server-load/action patterns already present in neighboring
  routes.
- Use `$lib` aliases for shared frontend code instead of long relative imports.
- Reuse shadcn-svelte primitives from `$lib/components/ui` and existing application components
  before creating new UI abstractions.
- Use `@lucide/svelte` for icons. Do not add the deprecated `lucide-svelte` package.
- Forms use `sveltekit-superforms` with Zod 4 adapters. Import public exports from the package root
  or documented subpaths; avoid reaching into package internals.
- Keep authenticated backend access on the server where existing routes do so, preserving the
  current HTTP-only cookie flow.
- Camera features require HTTPS outside localhost and must retain a manual fallback.

Prettier is the source of truth for frontend formatting:

- 100-character print width.
- Four spaces in TypeScript, JavaScript, and configuration files.
- Two spaces in `.svelte` files.
- No trailing commas.
- Let the Tailwind Prettier plugin order utility classes.

## Generated API client

The files under `frontend/src/lib/client/` are generated from the backend OpenAPI document. When an
API route or schema changes:

1. Update the backend implementation and tests.
2. Regenerate or refresh `frontend/openapi.json` from the running backend when required.
3. Run `bun run generate-client` from `frontend/`.
4. Review generated changes and run `bun run check` and `bun run build`.

Do not patch generated client files manually to work around a backend contract mismatch.

## Database and Docker safety

Typical local commands from the repository root are:

```bash
docker compose up -d db backend
docker compose exec backend uv run alembic upgrade head
docker compose logs -f backend
```

Changing values supplied through `.env` may require recreating a container:

```bash
docker compose up -d --force-recreate backend
```

Do not run `docker compose down -v` unless the user explicitly wants to delete the local PostgreSQL
volume and its data.

## Validation and handoff

Before considering a change complete:

- Run tests and static checks proportional to the change.
- Run `git diff --check`.
- Confirm no secrets, `.env` files, build output, or caches were added.
- Call out migrations, generated files, dependency changes, and non-blocking warnings in the
  handoff.
- Do not push, deploy, or open a pull request unless explicitly requested.
