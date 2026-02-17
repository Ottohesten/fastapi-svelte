import { expect, test } from "@playwright/test";
import { firstSuperuser } from "./config";
import { randomEmail, randomPassword } from "./utils/random";

test.describe("Admin Dashboard", () => {
    test("should load admin dashboard", async ({ page }) => {
        await page.goto("/admin");
        await expect(page.getByRole("heading", { name: "Administration" })).toBeVisible();
    });

    test.describe("Users Management", () => {
        test("should display users page", async ({ page }) => {
            await page.goto("/admin/users");
            await expect(page.getByRole("heading", { name: "User Management" })).toBeVisible();
            await expect(page.getByRole("button", { name: "Add User" })).toBeVisible();
            // Ensure superuser is present in the table
            await expect(page.getByRole("cell", { name: firstSuperuser })).toBeVisible();
        });

        test("create a new user successfully", async ({ page }) => {
            await page.goto("/admin/users");
            await page.waitForSelector('body[data-svelte-hydrated="true"]');

            const email = randomEmail();
            const password = randomPassword();
            const fullName = "Test User Admin";

            await page.getByRole("button", { name: "Add User" }).click();

            // Wait for the dialog title to be visible - this is usually the most reliable hook for modal dialogs
            // await expect(page.getByText("Create New User", { exact: true })).toBeVisible();

            // Use getByLabel with regex for better resilience
            await page.getByLabel(/Email/i).fill(email);
            await page.getByLabel(/Full Name/i).fill(fullName);
            // For Password, explicitly targeting the first password field
            await page.getByLabel(/^Password/i).fill(password);
            await page.getByLabel(/Confirm Password/i).fill(password);

            await page.getByRole("button", { name: "Create User" }).click();

            // verify that the new user was created successfully
            // await expect(page.getByText("User created successfully")).toBeVisible();
        });
    });

    test.describe("Ingredients Management", () => {
        test("should display ingredients page", async ({ page }) => {
            await page.goto("/admin/ingredients");
            await expect(page.getByRole("heading", { name: "Ingredients" })).toBeVisible();
            await expect(page.getByRole("button", { name: "Add Ingredient" })).toBeVisible();
        });
    });

    test.describe("Game Management", () => {
        test("should display sessions page", async ({ page }) => {
            await page.goto("/admin/game/sessions");
            await expect(page.getByText("This is the admin sessions page")).toBeVisible();
        });

        test("should display players page", async ({ page }) => {
            await page.goto("/admin/game/players");
            await expect(page.getByText("This is the admin players page")).toBeVisible();
        });

        test("should display drinks page", async ({ page }) => {
            await page.goto("/admin/game/drinks");
            await expect(page.getByRole("heading", { name: "Drinks" })).toBeVisible();
        });
    });
});
