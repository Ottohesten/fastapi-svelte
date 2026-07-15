import { describe, expect, test } from "bun:test";
import {
    ANALYTICS_ENDPOINT,
    buildPageMetrics,
    parsePageMetricBatch,
    postPageMetrics,
    toPublicRouteTemplate
} from "./page-metrics";
import { hasBrowserTelemetryOptOut, parseTracesSampleRate } from "./sentry-config";

describe("page metrics", () => {
    test("removes SvelteKit route groups without exposing concrete URLs", () => {
        expect(toPublicRouteTemplate("/(authed)/recipes/[slug]")).toBe("/recipes/[slug]");
        expect(toPublicRouteTemplate("/")).toBe("/");
    });

    test("records a page view and the first browser session", () => {
        expect(
            buildPageMetrics({
                routeId: "/(authed)/admin/users",
                browserSessionStarted: false
            })
        ).toEqual([
            {
                metric: "site.page_view",
                route: "/admin/users"
            },
            {
                metric: "site.browser_session.started",
                route: "/admin/users"
            }
        ]);
    });

    test("does not start the same browser session twice", () => {
        expect(
            buildPageMetrics({
                routeId: "/recipes",
                browserSessionStarted: true
            })
        ).toEqual([
            {
                metric: "site.page_view",
                route: "/recipes"
            }
        ]);
    });

    test("accepts a small metric batch and strips browser-supplied fields", () => {
        expect(
            parsePageMetricBatch({
                events: [
                    {
                        metric: "site.page_view",
                        route: "/recipes/[slug]",
                        authenticated: true,
                        url: "/recipes/a-private-slug"
                    }
                ]
            })
        ).toEqual({
            events: [{ metric: "site.page_view", route: "/recipes/[slug]" }]
        });
    });

    test("accepts optional and matcher route templates", () => {
        for (const route of ["/optional/[[language=locale]]", "/items/[id=uuid]"]) {
            expect(
                parsePageMetricBatch({
                    events: [{ metric: "site.page_view", route }]
                })
            ).toEqual({ events: [{ metric: "site.page_view", route }] });
        }
    });

    test("rejects invalid metrics, concrete URLs, and oversized batches", () => {
        expect(
            parsePageMetricBatch({ events: [{ metric: "unknown", route: "/recipes" }] })
        ).toBeNull();
        expect(
            parsePageMetricBatch({
                events: [{ metric: "site.page_view", route: "/recipes?private=value" }]
            })
        ).toBeNull();
        expect(
            parsePageMetricBatch({ events: [{ metric: "site.page_view", route: "//recipes" }] })
        ).toBeNull();
        expect(
            parsePageMetricBatch({
                events: Array.from({ length: 11 }, () => ({
                    metric: "site.page_view",
                    route: "/"
                }))
            })
        ).toBeNull();
    });

    test("posts metrics without propagating analytics failures", async () => {
        const requests: Array<{ input: string | URL | Request; init?: RequestInit }> = [];
        const successfulFetch = (async (input: string | URL | Request, init?: RequestInit) => {
            requests.push({ input, init });
            return new Response(null, { status: 204 });
        }) as typeof fetch;

        await postPageMetrics(
            [{ metric: "site.page_view", route: "/ingredients" }],
            successfulFetch
        );

        expect(requests).toHaveLength(1);
        expect(requests[0]?.input).toBe(ANALYTICS_ENDPOINT);
        expect(requests[0]?.init).toMatchObject({
            method: "POST",
            keepalive: true,
            body: JSON.stringify({
                events: [{ metric: "site.page_view", route: "/ingredients" }]
            })
        });

        const failingFetch = (() =>
            Promise.reject(new Error("offline"))) as unknown as typeof fetch;
        await expect(
            postPageMetrics([{ metric: "site.page_view", route: "/" }], failingFetch)
        ).resolves.toBeUndefined();
    });
});

describe("Sentry configuration", () => {
    test("accepts only valid trace sample rates", () => {
        expect(parseTracesSampleRate("0")).toBe(0);
        expect(parseTracesSampleRate("0.25")).toBe(0.25);
        expect(parseTracesSampleRate("2")).toBe(0.1);
        expect(parseTracesSampleRate("not-a-number")).toBe(0.1);
    });

    test("respects browser privacy signals", () => {
        expect(hasBrowserTelemetryOptOut({ doNotTrack: "1" } as Navigator)).toBe(true);
        expect(hasBrowserTelemetryOptOut({ doNotTrack: "yes" } as Navigator)).toBe(true);
        expect(
            hasBrowserTelemetryOptOut({
                doNotTrack: "0",
                globalPrivacyControl: true
            } as Navigator & { globalPrivacyControl: boolean })
        ).toBe(true);
        expect(hasBrowserTelemetryOptOut({ doNotTrack: "0" } as Navigator)).toBe(false);
    });
});
