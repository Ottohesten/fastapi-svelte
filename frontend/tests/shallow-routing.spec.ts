import { expect, test } from "@playwright/test";

test.describe("shallow overlay routing", () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test("browser history closes and restores the mobile navigation", async ({ page }) => {
        await page.goto("/");
        await page.waitForSelector('body[data-svelte-hydrated="true"]');
        const initialUrl = page.url();

        await page.getByRole("button", { name: "Open navigation" }).click();
        const navigation = page.getByRole("dialog");
        await expect(navigation).toBeVisible();

        // Browser back and a phone's back-swipe gesture traverse the same history entry.
        await page.goBack();
        await expect(page).toHaveURL(initialUrl);
        await expect(navigation).toBeHidden();

        await page.goForward();
        await expect(page).toHaveURL(initialUrl);
        await expect(navigation).toBeVisible();

        await navigation.getByRole("button", { name: "Close" }).click();
        await expect(navigation).toBeHidden();

        await page.goForward();
        await expect(navigation).toBeVisible();
    });

    test("browser history closes the admin mobile sidebar", async ({ page }) => {
        await page.goto("/admin/users");
        await page.waitForSelector('body[data-svelte-hydrated="true"]');
        const initialUrl = page.url();

        await page.getByRole("button", { name: "Toggle Sidebar" }).click();
        const sidebar = page.locator('[data-sidebar="sidebar"][data-mobile="true"]');
        await expect(sidebar).toBeVisible();

        await page.goBack();
        await expect(page).toHaveURL(initialUrl);
        await expect(sidebar).toBeHidden();
    });

    test("browser history closes and restores an admin dialog", async ({ page }) => {
        await page.goto("/admin/users");
        await page.waitForSelector('body[data-svelte-hydrated="true"]');
        const initialUrl = page.url();

        await page.getByRole("button", { name: "Add User" }).click();
        const dialog = page.getByRole("dialog", { name: "Create New User" });
        await expect(dialog).toBeVisible();

        await page.goBack();
        await expect(page).toHaveURL(initialUrl);
        await expect(dialog).toBeHidden();

        await page.goForward();
        await expect(dialog).toBeVisible();

        await dialog.getByRole("button", { name: "Cancel" }).click();
        await expect(dialog).toBeHidden();

        await page.goForward();
        await expect(dialog).toBeVisible();
    });
});
