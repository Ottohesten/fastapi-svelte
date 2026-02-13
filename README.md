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
   Create `.env` file in `backend/` directory:
   ```env
   PROJECT_NAME=FastAPI-Svelte
   ENVIRONMENT=local

   # Database
   POSTGRES_SERVER=localhost
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

3. **Generate API types** (optional, but recommended)
   ```bash
   bun run generate-client
   ```

4. **Start development server**
   ```bash
   bun run dev
   ```

   Frontend will be available at `http://localhost:5173`

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
```bash
cd backend
uv run pytest
```

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
