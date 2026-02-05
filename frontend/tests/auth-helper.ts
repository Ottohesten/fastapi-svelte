import type { Page } from "@playwright/test";

/**
 * Helper functions for authentication in tests
 */

export interface TestUser {
	email: string;
	password: string;
}

/**
 * Login a user via the UI
 */
export async function login(page: Page, user: TestUser) {
	await page.goto("/auth/login");
	await page.getByLabel(/email/i).fill(user.email);
	await page.getByLabel(/password/i).fill(user.password);
	await page.getByRole("button", { name: /login|sign in/i }).click();

	// Wait for navigation or success indicator
	await page.waitForURL(/^(?!.*\/auth\/login).*$/); // Wait until we're no longer on login page
}

/**
 * Logout the current user
 */
export async function logout(page: Page) {
	// Adjust selector based on your logout button implementation
	const logoutButton = page.getByRole("button", { name: /logout|sign out/i });
	if (await logoutButton.isVisible()) {
		await logoutButton.click();
	}
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
	// Check for auth indicators in your app (e.g., user menu, logout button)
	const logoutButton = page.getByRole("button", { name: /logout|sign out/i });
	return await logoutButton.isVisible();
}

// Test user credentials (use test/demo account)
export const TEST_USER: TestUser = {
	email: process.env.TEST_USER_EMAIL || "test@example.com",
	password: process.env.TEST_USER_PASSWORD || "testpassword123"
};
