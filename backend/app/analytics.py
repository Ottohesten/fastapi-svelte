from collections import Counter
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, col, select

from app.models import (
    AnalyticsAudienceSplitPublic,
    AnalyticsDailyCountPublic,
    AnalyticsEventCreate,
    AnalyticsHourlyBucket,
    AnalyticsMetricName,
    AnalyticsSummaryPublic,
    AnalyticsTopRoutePublic,
    AnalyticsTotalsPublic,
)


class AnalyticsStorageError(RuntimeError):
    """Raised when aggregate analytics storage is temporarily unavailable."""


ANALYTICS_RETENTION_DAYS = 90


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hour_start(value: datetime) -> datetime:
    return _as_utc(value).replace(minute=0, second=0, microsecond=0)


def record_analytics_events(
    session: Session,
    events: list[AnalyticsEventCreate],
    *,
    now: datetime | None = None,
) -> int:
    """Increment privacy-preserving hourly counters for a validated event batch."""
    bucket_start = _hour_start(now or _utc_now())
    increments: Counter[tuple[str, str, bool]] = Counter(
        (event.metric.value, event.route, bool(event.authenticated)) for event in events
    )
    values = [
        {
            "bucket_start": bucket_start,
            "metric_name": metric_name,
            "route": route,
            "authenticated": authenticated,
            "event_count": event_count,
        }
        for (metric_name, route, authenticated), event_count in increments.items()
    ]

    statement = insert(AnalyticsHourlyBucket).values(values)
    statement = statement.on_conflict_do_update(
        index_elements=[
            "bucket_start",
            "metric_name",
            "route",
            "authenticated",
        ],
        set_={
            "event_count": (
                AnalyticsHourlyBucket.event_count + statement.excluded.event_count
            )
        },
    )

    try:
        session.exec(
            delete(AnalyticsHourlyBucket).where(
                col(AnalyticsHourlyBucket.bucket_start)
                < bucket_start - timedelta(days=ANALYTICS_RETENTION_DAYS)
            )
        )
        session.exec(statement)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise AnalyticsStorageError from exc

    return len(events)


def get_analytics_summary(
    session: Session,
    *,
    now: datetime | None = None,
    top_route_limit: int = 5,
) -> AnalyticsSummaryPublic:
    """Build the admin summary exclusively from hourly aggregate rows."""
    generated_at = _as_utc(now or _utc_now())
    last_24_hours_start = generated_at - timedelta(hours=24)
    first_series_date = generated_at.date() - timedelta(days=6)
    first_series_start = datetime.combine(
        first_series_date, time.min, tzinfo=timezone.utc
    )
    last_7_days_start = first_series_start
    query_start = min(last_24_hours_start, first_series_start)
    next_hour = _hour_start(generated_at) + timedelta(hours=1)

    try:
        rows = session.exec(
            select(AnalyticsHourlyBucket).where(
                AnalyticsHourlyBucket.bucket_start >= query_start,
                AnalyticsHourlyBucket.bucket_start < next_hour,
            )
        ).all()
    except SQLAlchemyError as exc:
        raise AnalyticsStorageError from exc

    totals_24_hours = {
        AnalyticsMetricName.PAGE_VIEW: 0,
        AnalyticsMetricName.BROWSER_SESSION_STARTED: 0,
    }
    totals_7_days = {
        AnalyticsMetricName.PAGE_VIEW: 0,
        AnalyticsMetricName.BROWSER_SESSION_STARTED: 0,
    }
    daily_counts: dict[date, dict[AnalyticsMetricName, int]] = {
        first_series_date + timedelta(days=offset): {
            AnalyticsMetricName.PAGE_VIEW: 0,
            AnalyticsMetricName.BROWSER_SESSION_STARTED: 0,
        }
        for offset in range(7)
    }
    audience_counts = {True: 0, False: 0}
    route_counts: Counter[str] = Counter()

    for row in rows:
        bucket_start = _as_utc(row.bucket_start)
        try:
            metric_name = AnalyticsMetricName(row.metric_name)
        except ValueError:
            continue

        if bucket_start >= last_24_hours_start:
            totals_24_hours[metric_name] += row.event_count

        if bucket_start >= last_7_days_start:
            totals_7_days[metric_name] += row.event_count
            if metric_name is AnalyticsMetricName.PAGE_VIEW:
                audience_counts[row.authenticated] += row.event_count
                route_counts[row.route] += row.event_count

        day = bucket_start.date()
        if day in daily_counts:
            daily_counts[day][metric_name] += row.event_count

    top_routes = sorted(route_counts.items(), key=lambda item: (-item[1], item[0]))[
        :top_route_limit
    ]

    return AnalyticsSummaryPublic(
        generated_at=generated_at,
        last_24_hours=AnalyticsTotalsPublic(
            page_views=totals_24_hours[AnalyticsMetricName.PAGE_VIEW],
            browser_sessions=totals_24_hours[
                AnalyticsMetricName.BROWSER_SESSION_STARTED
            ],
        ),
        last_7_days=AnalyticsTotalsPublic(
            page_views=totals_7_days[AnalyticsMetricName.PAGE_VIEW],
            browser_sessions=totals_7_days[AnalyticsMetricName.BROWSER_SESSION_STARTED],
        ),
        daily_last_7_days=[
            AnalyticsDailyCountPublic(
                date=day,
                page_views=counts[AnalyticsMetricName.PAGE_VIEW],
                browser_sessions=counts[AnalyticsMetricName.BROWSER_SESSION_STARTED],
            )
            for day, counts in daily_counts.items()
        ],
        page_views_last_7_days_by_audience=AnalyticsAudienceSplitPublic(
            authenticated=audience_counts[True], anonymous=audience_counts[False]
        ),
        top_routes_last_7_days=[
            AnalyticsTopRoutePublic(route=route, page_views=count)
            for route, count in top_routes
        ],
    )
