import { expect, test } from "@playwright/test";
import { firstSuperuser, firstSuperuserPassword } from "./config";
import { randomEmail, randomPassword } from "./utils/random";

test("Admin page is accessible and shows correct title", async ({ page }) => {
	await page.goto("/admin");
	await expect(page.getByRole("heading", { name: "This is the admin page" })).toBeVisible();
	// await expect(
	//   page.getByText("Manage user accounts and permissions"),
	// ).toBeVisible()
});
