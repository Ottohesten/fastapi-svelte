import { expect, test, type Page } from "@playwright/test";

type PageMetricEvent = {
    metric: "site.page_view" | "site.browser_session.started";
    route: string;
};

async function interceptAnalytics(page: Page) {
    const batches: PageMetricEvent[][] = [];

    await page.route("**/analytics/events", async (route) => {
        const payload = route.request().postDataJSON() as { events?: PageMetricEvent[] };
        batches.push(payload.events ?? []);
        await route.fulfill({ status: 204 });
    });

    return {
        batches,
        events: () => batches.flat()
    };
}

test.describe("first-party traffic analytics", () => {
    test.beforeEach(async ({ page }) => {
        await page.addInitScript(() => {
            Object.defineProperty(navigator, "doNotTrack", {
                configurable: true,
                value: "0"
            });
            Object.defineProperty(navigator, "globalPrivacyControl", {
                configurable: true,
                value: false
            });
        });
    });

    test("records each page view and starts one session per tab", async ({ page }) => {
        const analytics = await interceptAnalytics(page);

        await page.goto("/");
        await expect
            .poll(() => analytics.events())
            .toEqual([
                { metric: "site.page_view", route: "/" },
                { metric: "site.browser_session.started", route: "/" }
            ]);

        await page.reload();
        await expect
            .poll(() => analytics.events())
            .toEqual([
                { metric: "site.page_view", route: "/" },
                { metric: "site.browser_session.started", route: "/" },
                { metric: "site.page_view", route: "/" }
            ]);
    });

    test("records a page view after SPA navigation", async ({ page }) => {
        const analytics = await interceptAnalytics(page);

        await page.goto("/auth/login");
        await expect.poll(() => analytics.events().length).toBe(2);

        await page.getByRole("link", { name: "Internationaleregler" }).click();
        await expect(page).toHaveURL("/");
        await expect
            .poll(() => analytics.events())
            .toEqual([
                { metric: "site.page_view", route: "/auth/login" },
                { metric: "site.browser_session.started", route: "/auth/login" },
                { metric: "site.page_view", route: "/" }
            ]);
    });

    test("does not count shallow overlay history as a page view", async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        const analytics = await interceptAnalytics(page);

        await page.goto("/");
        await expect.poll(() => analytics.events().length).toBe(2);

        await page.getByRole("button", { name: "Open navigation" }).click();
        const navigation = page.getByRole("dialog");
        await expect(navigation).toBeVisible();

        await page.goBack();
        await expect(navigation).toBeHidden();

        await page.waitForLoadState("networkidle");
        expect(analytics.events()).toEqual([
            { metric: "site.page_view", route: "/" },
            { metric: "site.browser_session.started", route: "/" }
        ]);
    });
});
