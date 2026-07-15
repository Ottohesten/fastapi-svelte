from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlmodel import Session, select

import app.analytics as analytics_service
from app.analytics import AnalyticsStorageError
from app.config import settings
from app.models import (
    AnalyticsEventBatchCreate,
    AnalyticsEventCreate,
    AnalyticsHourlyBucket,
    AnalyticsMetricName,
)


FIXED_NOW = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
INGEST_TOKEN = "test-only-analytics-ingest-token"
INGEST_HEADERS = {"X-Analytics-Ingest-Token": INGEST_TOKEN}


@pytest.fixture(autouse=True)
def configured_ingest_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ANALYTICS_INGEST_TOKEN", SecretStr(INGEST_TOKEN))


@pytest.mark.no_db
@pytest.mark.parametrize(
    "route",
    [
        "/",
        "/ingredients",
        "/recipes/[slug]",
        "/game/[game_session_id]/player/[player_id]",
        "/optional/[[language=locale]]",
        "/files/[...path]",
    ],
)
def test_analytics_event_accepts_svelte_route_templates(route: str) -> None:
    event = AnalyticsEventCreate(
        metric=AnalyticsMetricName.PAGE_VIEW,
        route=route,
        authenticated=False,
    )

    assert event.route == route


@pytest.mark.no_db
@pytest.mark.parametrize(
    "route",
    [
        "recipes",
        "/recipes/",
        "/recipes?draft=true",
        "/recipes#top",
        "https://example.com/recipes",
        "/(authed)/admin",
        "/recipes/[invalid parameter]",
    ],
)
def test_analytics_event_rejects_invalid_route_templates(route: str) -> None:
    with pytest.raises(ValidationError, match="valid Svelte route template"):
        AnalyticsEventCreate(
            metric=AnalyticsMetricName.PAGE_VIEW,
            route=route,
            authenticated=False,
        )


@pytest.mark.no_db
def test_analytics_payload_rejects_unknown_metrics_and_non_boolean_audience() -> None:
    with pytest.raises(ValidationError):
        AnalyticsEventCreate.model_validate(
            {
                "metric": "site.identifiable_user",
                "route": "/",
                "authenticated": False,
            }
        )

    with pytest.raises(ValidationError, match="valid boolean"):
        AnalyticsEventCreate.model_validate(
            {
                "metric": "site.page_view",
                "route": "/",
                "authenticated": "true",
            }
        )


@pytest.mark.no_db
def test_analytics_batch_is_bounded_and_model_has_no_identifying_fields() -> None:
    event = AnalyticsEventCreate(
        metric=AnalyticsMetricName.PAGE_VIEW,
        route="/",
        authenticated=False,
    )

    with pytest.raises(ValidationError):
        AnalyticsEventBatchCreate(events=[])
    with pytest.raises(ValidationError):
        AnalyticsEventBatchCreate(events=[event] * 51)

    assert set(AnalyticsHourlyBucket.model_fields) == {
        "bucket_start",
        "metric_name",
        "route",
        "authenticated",
        "event_count",
    }


def test_ingest_analytics_events_upserts_hourly_aggregates(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analytics_service, "_utc_now", lambda: FIXED_NOW)
    payload = {
        "events": [
            {
                "metric": "site.page_view",
                "route": "/recipes/[slug]",
                "authenticated": True,
            },
            {
                "metric": "site.page_view",
                "route": "/recipes/[slug]",
                "authenticated": True,
            },
            {
                "metric": "site.browser_session.started",
                "route": "/recipes/[slug]",
                "authenticated": True,
            },
        ]
    }

    response = client.post("/analytics/events", json=payload, headers=INGEST_HEADERS)
    second_response = client.post(
        "/analytics/events",
        json={"events": [payload["events"][0]]},
        headers=INGEST_HEADERS,
    )

    assert response.status_code == 202
    assert response.json() == {"accepted": 3}
    assert second_response.status_code == 202
    assert second_response.json() == {"accepted": 1}

    rows = db.exec(select(AnalyticsHourlyBucket)).all()
    counts = {
        (row.metric_name, row.route, row.authenticated): row.event_count for row in rows
    }
    assert counts == {
        ("site.page_view", "/recipes/[slug]", True): 3,
        ("site.browser_session.started", "/recipes/[slug]", True): 1,
    }
    assert {row.bucket_start for row in rows} == {FIXED_NOW}


@pytest.mark.parametrize(
    "event",
    [
        {"metric": "site.unknown", "route": "/", "authenticated": False},
        {
            "metric": "site.page_view",
            "route": "https://example.com/",
            "authenticated": False,
        },
        {"metric": "site.page_view", "route": "/", "authenticated": "false"},
    ],
)
def test_ingest_analytics_events_rejects_invalid_dimensions(
    client: TestClient, db: Session, event: dict[str, object]
) -> None:
    response = client.post(
        "/analytics/events", json={"events": [event]}, headers=INGEST_HEADERS
    )

    assert response.status_code == 422
    assert db.exec(select(AnalyticsHourlyBucket)).all() == []


def _add_bucket(
    db: Session,
    *,
    bucket_start: datetime,
    metric_name: AnalyticsMetricName,
    route: str,
    authenticated: bool,
    event_count: int,
) -> None:
    db.add(
        AnalyticsHourlyBucket(
            bucket_start=bucket_start,
            metric_name=metric_name.value,
            route=route,
            authenticated=authenticated,
            event_count=event_count,
        )
    )


def test_ingest_analytics_events_requires_server_token(
    client: TestClient, db: Session
) -> None:
    payload = {
        "events": [
            {
                "metric": "site.page_view",
                "route": "/",
                "authenticated": False,
            }
        ]
    }

    missing = client.post("/analytics/events", json=payload)
    incorrect = client.post(
        "/analytics/events",
        json=payload,
        headers={"X-Analytics-Ingest-Token": "incorrect"},
    )

    assert missing.status_code == 401
    assert incorrect.status_code == 401
    assert db.exec(select(AnalyticsHourlyBucket)).all() == []


def test_ingest_analytics_events_is_unavailable_without_configured_token(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ANALYTICS_INGEST_TOKEN", None)

    response = client.post(
        "/analytics/events",
        json={
            "events": [
                {
                    "metric": "site.page_view",
                    "route": "/",
                    "authenticated": False,
                }
            ]
        },
        headers=INGEST_HEADERS,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Analytics ingestion is not configured."}
    assert db.exec(select(AnalyticsHourlyBucket)).all() == []


def test_ingest_prunes_expired_aggregate_buckets(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analytics_service, "_utc_now", lambda: FIXED_NOW)
    _add_bucket(
        db,
        bucket_start=FIXED_NOW - timedelta(days=91),
        metric_name=AnalyticsMetricName.PAGE_VIEW,
        route="/old",
        authenticated=False,
        event_count=10,
    )
    _add_bucket(
        db,
        bucket_start=FIXED_NOW - timedelta(days=90),
        metric_name=AnalyticsMetricName.PAGE_VIEW,
        route="/retention-boundary",
        authenticated=False,
        event_count=5,
    )
    db.commit()

    response = client.post(
        "/analytics/events",
        json={
            "events": [
                {
                    "metric": "site.page_view",
                    "route": "/",
                    "authenticated": False,
                }
            ]
        },
        headers=INGEST_HEADERS,
    )

    assert response.status_code == 202
    rows = db.exec(select(AnalyticsHourlyBucket)).all()
    assert {row.route: row.event_count for row in rows} == {
        "/": 1,
        "/retention-boundary": 5,
    }


def test_admin_analytics_summary_returns_expected_aggregates(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analytics_service, "_utc_now", lambda: FIXED_NOW)
    buckets = [
        (
            timedelta(hours=-1),
            AnalyticsMetricName.PAGE_VIEW,
            "/recipes/[slug]",
            True,
            5,
        ),
        (
            timedelta(hours=-1),
            AnalyticsMetricName.PAGE_VIEW,
            "/recipes/[slug]",
            False,
            3,
        ),
        (
            timedelta(hours=-1),
            AnalyticsMetricName.BROWSER_SESSION_STARTED,
            "/recipes/[slug]",
            False,
            2,
        ),
        (timedelta(hours=-23), AnalyticsMetricName.PAGE_VIEW, "/ingredients", False, 4),
        (timedelta(days=-6, hours=1), AnalyticsMetricName.PAGE_VIEW, "/", True, 7),
        (
            timedelta(days=-6, hours=1),
            AnalyticsMetricName.BROWSER_SESSION_STARTED,
            "/",
            True,
            1,
        ),
        (timedelta(days=-8), AnalyticsMetricName.PAGE_VIEW, "/old", False, 100),
    ]
    for offset, metric_name, route, authenticated, event_count in buckets:
        _add_bucket(
            db,
            bucket_start=FIXED_NOW + offset,
            metric_name=metric_name,
            route=route,
            authenticated=authenticated,
            event_count=event_count,
        )
    db.commit()

    response = client.get("/analytics/admin/summary", headers=superuser_token_headers)

    assert response.status_code == 200
    summary = response.json()
    assert summary["generated_at"] == "2026-07-15T12:00:00Z"
    assert summary["last_24_hours"] == {
        "page_views": 12,
        "browser_sessions": 2,
    }
    assert summary["last_7_days"] == {
        "page_views": 19,
        "browser_sessions": 3,
    }
    assert summary["page_views_last_7_days_by_audience"] == {
        "authenticated": 12,
        "anonymous": 7,
    }
    assert summary["top_routes_last_7_days"] == [
        {"route": "/recipes/[slug]", "page_views": 8},
        {"route": "/", "page_views": 7},
        {"route": "/ingredients", "page_views": 4},
    ]
    assert summary["daily_last_7_days"] == [
        {"date": "2026-07-09", "page_views": 7, "browser_sessions": 1},
        {"date": "2026-07-10", "page_views": 0, "browser_sessions": 0},
        {"date": "2026-07-11", "page_views": 0, "browser_sessions": 0},
        {"date": "2026-07-12", "page_views": 0, "browser_sessions": 0},
        {"date": "2026-07-13", "page_views": 0, "browser_sessions": 0},
        {"date": "2026-07-14", "page_views": 4, "browser_sessions": 0},
        {"date": "2026-07-15", "page_views": 8, "browser_sessions": 2},
    ]


def test_admin_analytics_summary_requires_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    anonymous_response = client.get("/analytics/admin/summary")
    normal_user_response = client.get(
        "/analytics/admin/summary", headers=normal_user_token_headers
    )

    assert anonymous_response.status_code == 401
    assert normal_user_response.status_code == 403


def test_analytics_endpoints_hide_storage_errors(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise AnalyticsStorageError("sensitive database details")

    monkeypatch.setattr("app.routers.analytics.record_analytics_events", fail)
    monkeypatch.setattr("app.routers.analytics.get_analytics_summary", fail)

    ingest_response = client.post(
        "/analytics/events",
        json={
            "events": [
                {
                    "metric": "site.page_view",
                    "route": "/",
                    "authenticated": False,
                }
            ]
        },
        headers=INGEST_HEADERS,
    )
    summary_response = client.get(
        "/analytics/admin/summary", headers=superuser_token_headers
    )

    for response in (ingest_response, summary_response):
        assert response.status_code == 503
        assert response.json() == {
            "detail": "Analytics are temporarily unavailable. Please try again."
        }
        assert "sensitive" not in response.text
