export type DailyTraffic = {
    date: string;
    page_views: number;
    browser_sessions: number;
};

export type TopRouteTraffic = {
    route: string;
    page_views: number;
};

export type TrafficData = {
    page_views_24h: number;
    page_views_7d: number;
    browser_sessions_7d: number;
    authenticated_page_views_7d: number;
    anonymous_page_views_7d: number;
    daily: DailyTraffic[];
    top_routes: TopRouteTraffic[];
};

export function isTrafficData(value: unknown): value is TrafficData {
    if (!isRecord(value)) return false;

    return (
        isNonNegativeNumber(value.page_views_24h) &&
        isNonNegativeNumber(value.page_views_7d) &&
        isNonNegativeNumber(value.browser_sessions_7d) &&
        isNonNegativeNumber(value.authenticated_page_views_7d) &&
        isNonNegativeNumber(value.anonymous_page_views_7d) &&
        Array.isArray(value.daily) &&
        value.daily.every(isDailyTraffic) &&
        Array.isArray(value.top_routes) &&
        value.top_routes.every(isTopRouteTraffic)
    );
}

function isDailyTraffic(value: unknown): value is DailyTraffic {
    return (
        isRecord(value) &&
        typeof value.date === "string" &&
        /^\d{4}-\d{2}-\d{2}$/.test(value.date) &&
        isNonNegativeNumber(value.page_views) &&
        isNonNegativeNumber(value.browser_sessions)
    );
}

function isTopRouteTraffic(value: unknown): value is TopRouteTraffic {
    return (
        isRecord(value) && typeof value.route === "string" && isNonNegativeNumber(value.page_views)
    );
}

function isNonNegativeNumber(value: unknown): value is number {
    return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
