import { expect, test } from "@playwright/test";
import { firstSuperuser } from "./config";
import { randomEmail, randomPassword } from "./utils/random";

test.describe("Admin Dashboard", () => {
    test("should load admin dashboard", async ({ page }) => {
        await page.goto("/admin");
        await expect(page.getByRole("heading", { name: "Administration" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Traffic" })).toBeVisible();
    });

    test.describe("Users Management", () => {
        test("should display users page", async ({ page }) => {
            await page.goto("/admin/users");
            await expect(page.getByRole("heading", { name: "User Management" })).toBeVisible();
            await expect(page.getByRole("button", { name: "Add User" })).toBeVisible();
            // Ensure superuser is present in the table
            await expect(
                page.getByRole("cell", { name: firstSuperuser, exact: true })
            ).toBeVisible();
        });

        test("create a new user successfully", async ({ page }) => {
            await page.goto("/admin/users");
            await page.waitForSelector('body[data-svelte-hydrated="true"]');

            const email = randomEmail();
            const password = randomPassword();
            const fullName = "Test User Admin";

            await page.getByRole("button", { name: "Add User", exact: true }).click();
            const dialog = page.getByRole("dialog", { name: "Create New User" });
            await expect(dialog).toBeVisible();

            await dialog.getByLabel(/^Email \*$/i).fill(email);
            await dialog.getByLabel(/^Full Name \*$/i).fill(fullName);
            await dialog.getByLabel(/^Password \*$/i).fill(password);
            await dialog.getByLabel(/^Confirm Password \*$/i).fill(password);

            await dialog.getByRole("button", { name: "Create User", exact: true }).click();

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

        test.describe("phone barcode scanner", () => {
            test.use({ viewport: { width: 390, height: 844 } });

            test("uses portrait width and survives rotation into the ingredient form", async ({
                page
            }) => {
                const barcode = "5701234567890";
                await page.route(`**/admin/ingredients/barcode/${barcode}`, async (route) => {
                    await route.fulfill({
                        status: 200,
                        contentType: "application/json",
                        body: JSON.stringify({
                            barcode,
                            title: "Landscape test product",
                            brand: "Test foods",
                            image_url: null,
                            calories: 240,
                            carbohydrates: 30,
                            fat: 8,
                            protein: 12,
                            weight_per_piece: 100,
                            nutrition_basis: "100g",
                            missing_nutrients: [],
                            existing_ingredient_id: null
                        })
                    });
                });

                await page.goto("/admin/ingredients");
                await page.waitForSelector('body[data-svelte-hydrated="true"]');
                await page.getByRole("button", { name: "Add Ingredient" }).click();
                await page.getByRole("button", { name: "Scan product barcode" }).click();

                const scanDialog = page.getByRole("dialog", { name: "Scan a barcode" });
                const camera = scanDialog.getByTestId("barcode-camera-preview");
                const controls = scanDialog.getByTestId("barcode-scanner-controls");
                await expect(camera).toBeVisible();
                await expect(controls).toBeVisible();
                await expect
                    .poll(async () => (await scanDialog.boundingBox())?.width ?? 0)
                    .toBeGreaterThanOrEqual(389);

                const [portraitDialogBox, portraitCameraBox, portraitControlsBox] =
                    await Promise.all([
                        scanDialog.boundingBox(),
                        camera.boundingBox(),
                        controls.boundingBox()
                    ]);
                expect(portraitDialogBox).not.toBeNull();
                expect(portraitCameraBox).not.toBeNull();
                expect(portraitControlsBox).not.toBeNull();
                if (!portraitDialogBox || !portraitCameraBox || !portraitControlsBox) return;

                expect(portraitCameraBox.width).toBeGreaterThan(350);
                expect(portraitControlsBox.y).toBeGreaterThanOrEqual(
                    portraitCameraBox.y + portraitCameraBox.height
                );

                await page.setViewportSize({ width: 844, height: 390 });
                await expect
                    .poll(async () => (await scanDialog.boundingBox())?.width ?? 0)
                    .toBeGreaterThan(700);

                const [dialogBox, cameraBox, controlsBox] = await Promise.all([
                    scanDialog.boundingBox(),
                    camera.boundingBox(),
                    controls.boundingBox()
                ]);
                expect(dialogBox).not.toBeNull();
                expect(cameraBox).not.toBeNull();
                expect(controlsBox).not.toBeNull();
                if (!dialogBox || !cameraBox || !controlsBox) return;

                expect(dialogBox.y).toBeGreaterThanOrEqual(-4);
                expect(dialogBox.y + dialogBox.height).toBeLessThanOrEqual(394);
                expect(controlsBox.x).toBeGreaterThanOrEqual(cameraBox.x + cameraBox.width);

                await scanDialog.getByPlaceholder("Enter barcode manually").fill(barcode);
                await scanDialog.getByRole("button", { name: "Look up" }).click();

                const ingredientDialog = page.getByRole("dialog", { name: "Add New Ingredient" });
                await expect(ingredientDialog.getByLabel("Protein (per 100g)")).toHaveValue("12");
                await expect
                    .poll(() =>
                        page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)
                    )
                    .toBe(true);
            });
        });
    });

    test.describe("Game Management", () => {
        test("should display sessions page", async ({ page }) => {
            await page.goto("/admin/game/sessions");
            await expect(page.getByRole("heading", { name: "Game sessions" })).toBeVisible();
        });

        test("should display players page", async ({ page }) => {
            await page.goto("/admin/game/players");
            await expect(page.getByRole("heading", { name: "Players" })).toBeVisible();
        });

        test("should display drinks page", async ({ page }) => {
            await page.goto("/admin/game/drinks");
            await expect(page.getByRole("heading", { name: "Drinks" })).toBeVisible();
        });
    });
});
