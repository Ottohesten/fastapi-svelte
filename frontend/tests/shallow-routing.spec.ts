import { expect, test, type Page } from "@playwright/test";

async function expectOverlayCount(page: Page, count: number) {
    await expect
        .poll(() =>
            page.evaluate(() => {
                const pageState = history.state?.["sveltekit:states"] as
                    { shallowOverlays?: string[] } | undefined;
                return pageState?.shallowOverlays?.length ?? 0;
            })
        )
        .toBe(count);
}

test.describe("shallow overlay routing", () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test("browser history closes and restores the mobile navigation", async ({ page }) => {
        await page.goto("/");
        const initialUrl = page.url();

        await page.getByRole("button", { name: "Open navigation" }).click();
        const navigation = page.getByRole("dialog");
        await expect(navigation).toBeVisible();
        await expectOverlayCount(page, 1);

        // Browser back and a phone's back-swipe gesture traverse the same history entry.
        await page.goBack();
        await expect(page).toHaveURL(initialUrl);
        await expect(navigation).toBeHidden();
        await expectOverlayCount(page, 0);

        await page.goForward();
        await expect(page).toHaveURL(initialUrl);
        await expect(navigation).toBeVisible();
        await expectOverlayCount(page, 1);

        await navigation.getByRole("button", { name: "Close" }).click();
        await expect(navigation).toBeHidden();
        await expectOverlayCount(page, 0);

        await page.goForward();
        await expect(navigation).toBeVisible();
        await expectOverlayCount(page, 1);
    });

    test("browser history closes the admin mobile sidebar", async ({ page }) => {
        await page.goto("/admin/users");
        const initialUrl = page.url();

        await page.getByRole("button", { name: "Toggle Sidebar" }).click();
        const sidebar = page.locator('[data-sidebar="sidebar"][data-mobile="true"]');
        await expect(sidebar).toBeVisible();
        await expectOverlayCount(page, 1);

        await page.goBack();
        await expect(page).toHaveURL(initialUrl);
        await expect(sidebar).toBeHidden();
        await expectOverlayCount(page, 0);
    });

    test("browser history closes and restores an admin dialog", async ({ page }) => {
        await page.goto("/admin/users");
        const initialUrl = page.url();

        await page.getByRole("button", { name: "Add User" }).click();
        const dialog = page.getByRole("dialog", { name: "Create New User" });
        await expect(dialog).toBeVisible();
        await expectOverlayCount(page, 1);

        await page.goBack();
        await expect(page).toHaveURL(initialUrl);
        await expect(dialog).toBeHidden();
        await expectOverlayCount(page, 0);

        await page.goForward();
        await expect(dialog).toBeVisible();
        await expectOverlayCount(page, 1);

        await dialog.getByRole("button", { name: "Cancel" }).click();
        await expect(dialog).toBeHidden();
        await expectOverlayCount(page, 0);

        await page.goForward();
        await expect(dialog).toBeVisible();
        await expectOverlayCount(page, 1);
    });
});
