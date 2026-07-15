import sentry_sdk
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.config import settings
from app.routers import (
    analytics,
    users,
    login,
    recipes,
    ingredients,
    game,
    roles,
    utils,
)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        send_default_pii=settings.SENTRY_SEND_DEFAULT_PII,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        enable_metrics=False,
        # Distinguish events from local, staging, and production environments.
        environment=settings.ENVIRONMENT,
    )


# app = FastAPI(dependencies=[Depends(oauth2_scheme)])
# app = FastAPI(swagger_ui_parameters={"persistAuthorization": True})
app = FastAPI(
    title=settings.PROJECT_NAME, generate_unique_id_function=custom_generate_unique_id
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(login.router)
app.include_router(users.router)
app.include_router(utils.router)
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(game.router)
app.include_router(roles.router)
app.include_router(analytics.router)
