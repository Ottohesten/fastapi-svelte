import { describe, expect, test } from "bun:test";
import { isTrafficData } from "./analytics";

const traffic = {
    page_views_24h: 12,
    page_views_7d: 42,
    browser_sessions_7d: 9,
    authenticated_page_views_7d: 30,
    anonymous_page_views_7d: 12,
    daily: [{ date: "2026-07-15", page_views: 12, browser_sessions: 3 }],
    top_routes: [{ route: "/recipes/[slug]", page_views: 8 }]
};

describe("admin traffic response validation", () => {
    test("accepts the expected aggregate response", () => {
        expect(isTrafficData(traffic)).toBe(true);
    });

    test("rejects malformed or negative aggregates", () => {
        expect(isTrafficData({ ...traffic, page_views_24h: -1 })).toBe(false);
        expect(
            isTrafficData({
                ...traffic,
                daily: [{ date: "15/07/2026", page_views: 12, browser_sessions: 3 }]
            })
        ).toBe(false);
        expect(isTrafficData({ ...traffic, top_routes: [{ route: "/", page_views: "8" }] })).toBe(
            false
        );
    });
});
