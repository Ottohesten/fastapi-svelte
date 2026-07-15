import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.analytics import (
    AnalyticsStorageError,
    get_analytics_summary,
    record_analytics_events,
)
from app.config import settings
from app.deps import SessionDep, get_current_active_superuser
from app.models import (
    AnalyticsEventBatchCreate,
    AnalyticsIngestResponse,
    AnalyticsSummaryPublic,
    User,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


def require_analytics_ingest_token(
    supplied_token: Annotated[
        str | None,
        Header(alias="X-Analytics-Ingest-Token", min_length=1, max_length=256),
    ] = None,
) -> None:
    configured_token = settings.ANALYTICS_INGEST_TOKEN
    if configured_token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics ingestion is not configured.",
        )

    if supplied_token is None or not secrets.compare_digest(
        supplied_token.encode(), configured_token.get_secret_value().encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )


@router.post(
    "/events",
    response_model=AnalyticsIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def ingest_analytics_events(
    payload: AnalyticsEventBatchCreate,
    session: SessionDep,
    _authorized: Annotated[None, Depends(require_analytics_ingest_token)],
) -> AnalyticsIngestResponse:
    """Add a batch to non-identifying hourly counters without retaining raw events."""
    try:
        accepted = record_analytics_events(session, payload.events)
    except AnalyticsStorageError:
        logger.exception("Could not store analytics aggregate batch")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics are temporarily unavailable. Please try again.",
        ) from None

    return AnalyticsIngestResponse(accepted=accepted)


@router.get("/admin/summary", response_model=AnalyticsSummaryPublic)
def get_admin_analytics_summary(
    session: SessionDep,
    _current_user: Annotated[User, Depends(get_current_active_superuser)],
) -> AnalyticsSummaryPublic:
    """Return aggregate traffic data to active superusers only."""
    try:
        return get_analytics_summary(session)
    except AnalyticsStorageError:
        logger.exception("Could not read analytics summary")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics are temporarily unavailable. Please try again.",
        ) from None
