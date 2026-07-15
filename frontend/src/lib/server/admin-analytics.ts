import type { TrafficData } from "$lib/analytics";
import { AnalyticsService } from "$lib/client/sdk.gen.js";

const ANALYTICS_REQUEST_TIMEOUT_MS = 5_000;

export async function loadAdminTraffic(
    authToken: string | undefined,
    { signal }: { signal?: AbortSignal } = {}
): Promise<TrafficData | null> {
    if (!authToken) return null;

    const controller = new AbortController();
    const abortFromParent = () => controller.abort();
    if (signal?.aborted) {
        controller.abort();
    } else {
        signal?.addEventListener("abort", abortFromParent, { once: true });
    }
    const timeout = setTimeout(() => controller.abort(), ANALYTICS_REQUEST_TIMEOUT_MS);

    try {
        const { data, error } = await AnalyticsService.GetAdminAnalyticsSummary({
            auth: authToken,
            signal: controller.signal
        });
        if (error || !data) return null;

        return {
            page_views_24h: data.last_24_hours.page_views,
            page_views_7d: data.last_7_days.page_views,
            browser_sessions_7d: data.last_7_days.browser_sessions,
            authenticated_page_views_7d: data.page_views_last_7_days_by_audience.authenticated,
            anonymous_page_views_7d: data.page_views_last_7_days_by_audience.anonymous,
            daily: data.daily_last_7_days.map((day) => ({
                date: day.date.toISOString().slice(0, 10),
                page_views: day.page_views,
                browser_sessions: day.browser_sessions
            })),
            top_routes: data.top_routes_last_7_days
        };
    } catch {
        return null;
    } finally {
        clearTimeout(timeout);
        signal?.removeEventListener("abort", abortFromParent);
    }
}
