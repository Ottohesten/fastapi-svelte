export const BROWSER_SESSION_STORAGE_KEY = "site-metrics:browser-session-started";

export const ANALYTICS_ENDPOINT = "/analytics/events";

export type PageMetricName = "site.page_view" | "site.browser_session.started";

export type PageMetricEvent = {
    metric: PageMetricName;
    route: string;
};

export type PageMetricBatch = { events: PageMetricEvent[] };

const MAX_BATCH_SIZE = 10;
const MAX_ROUTE_LENGTH = 200;
const ROUTE_PARAMETER = String.raw`(?:\.\.\.)?[A-Za-z_][A-Za-z0-9_]*(?:=[A-Za-z_][A-Za-z0-9_]*)?`;
const ROUTE_SEGMENT = String.raw`(?:[A-Za-z0-9._~-]+|\[${ROUTE_PARAMETER}\]|\[\[${ROUTE_PARAMETER}\]\])`;
const ROUTE_TEMPLATE_PATTERN = new RegExp(
    String.raw`^/(?:${ROUTE_SEGMENT}(?:/${ROUTE_SEGMENT})*)?$`
);

export function toPublicRouteTemplate(routeId: string): string {
    const routeWithoutGroups = routeId.replace(/\/\([^/]+\)/g, "");
    return routeWithoutGroups || "/";
}

export function buildPageMetrics({
    routeId,
    browserSessionStarted
}: {
    routeId: string;
    browserSessionStarted: boolean;
}): PageMetricEvent[] {
    const route = toPublicRouteTemplate(routeId);
    const pageView: PageMetricEvent = {
        metric: "site.page_view",
        route
    };

    if (browserSessionStarted) return [pageView];

    return [
        pageView,
        {
            metric: "site.browser_session.started",
            route
        }
    ];
}

export function parsePageMetricBatch(value: unknown): PageMetricBatch | null {
    if (!isRecord(value) || !Array.isArray(value.events)) return null;
    if (value.events.length === 0 || value.events.length > MAX_BATCH_SIZE) return null;

    const events: PageMetricEvent[] = [];
    for (const event of value.events) {
        if (!isRecord(event)) return null;
        if (event.metric !== "site.page_view" && event.metric !== "site.browser_session.started") {
            return null;
        }
        if (
            typeof event.route !== "string" ||
            event.route.length > MAX_ROUTE_LENGTH ||
            !ROUTE_TEMPLATE_PATTERN.test(event.route)
        ) {
            return null;
        }

        events.push({ metric: event.metric, route: event.route });
    }

    return { events };
}

export async function postPageMetrics(
    events: PageMetricEvent[],
    fetchImplementation: typeof fetch = fetch
): Promise<void> {
    if (events.length === 0) return;

    try {
        await fetchImplementation(ANALYTICS_ENDPOINT, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ events }),
            keepalive: true
        });
    } catch {
        // Analytics must never affect navigation or application behavior.
    }
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
