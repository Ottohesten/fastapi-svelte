import { test, expect } from "@playwright/test";

test.describe("Homepage", () => {
	test("should load the homepage", async ({ page }) => {
		await page.goto("/");
		await expect(page).toHaveTitle(/Internationaleregler/);
	});

	test("should have navigation links", async ({ page }) => {
		await page.goto("/");
		await expect(page.getByRole("link", { name: /game/i })).toBeVisible();
	});
});

test.describe("Authentication", () => {
	test("should show login page", async ({ page }) => {
		await page.goto("/auth/login");
		await expect(page.getByRole("heading", { name: /login|sign in/i })).toBeVisible();
	});

	test("should display login form", async ({ page }) => {
		await page.goto("/auth/login");
		await expect(page.getByLabel(/email/i)).toBeVisible();
		await expect(page.getByLabel(/password/i)).toBeVisible();
		await expect(page.getByRole("button", { name: /login|sign in/i })).toBeVisible();
	});

	test("should show error on invalid login", async ({ page }) => {
		await page.goto("/auth/login");
		await page.getByLabel(/email/i).fill("invalid@example.com");
		await page.getByLabel(/password/i).fill("wrongpassword");
		await page.getByRole("button", { name: /login|sign in/i }).click();

		// Wait for error message (adjust selector based on your error display)
		await expect(page.getByText(/incorrect|invalid|error/i)).toBeVisible();
	});
});

test.describe("Recipes", () => {
	test("should display recipes list page", async ({ page }) => {
		await page.goto("/recipes");
		await expect(page.getByRole("heading", { name: /recipes/i })).toBeVisible();
	});

	test("should redirect to login when trying to create recipe without auth", async ({ page }) => {
		// Try to access create recipe page without being authenticated
		await page.goto("/recipes/create");

		// Should be redirected to login page
		await expect(page).toHaveURL(/\/auth\/login/);

		// Should show login form
		await expect(page.getByLabel(/email/i)).toBeVisible();
	});
});

test.describe("Ingredients", () => {
	test("should display ingredients page", async ({ page }) => {
		await page.goto("/ingredients");
		await expect(page.getByRole("heading", { name: /ingredients/i })).toBeVisible();
	});
});
