import { expect, test, type Locator, type Page } from "@playwright/test";

function uniqueValue(prefix: string): string {
    return `${prefix} ${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function productRow(page: Page, title: string) {
    return page.getByRole("row").filter({ hasText: title });
}

function diaryEntry(page: Page, title: string) {
    return page.locator("article").filter({ hasText: title });
}

async function gotoHydrated(page: Page, url: string) {
    await page.goto(url);
    await page.waitForSelector('body[data-svelte-hydrated="true"]');
}

async function acceptNextConfirmation(page: Page) {
    page.once("dialog", (dialog) => dialog.accept());
}

async function expectFieldStacked(scope: Locator, control: Locator) {
    const id = await control.getAttribute("id");
    expect(id, "Formsnap should connect every visible control to its label").toBeTruthy();
    const label = scope.locator(`label[for="${id}"]`);
    await expect(label).toHaveCount(1);

    const [labelBox, controlBox] = await Promise.all([label.boundingBox(), control.boundingBox()]);
    expect(labelBox).not.toBeNull();
    expect(controlBox).not.toBeNull();
    if (!labelBox || !controlBox) return;

    expect(Math.abs(labelBox.x - controlBox.x)).toBeLessThanOrEqual(4);
    expect(controlBox.y).toBeGreaterThanOrEqual(labelBox.y + labelBox.height);
}

async function deleteProductIfPresent(page: Page, title: string) {
    await gotoHydrated(page, `/products?query=${encodeURIComponent(title)}`);
    const row = productRow(page, title);
    if ((await row.count()) === 0) return;

    await acceptNextConfirmation(page);
    await row.getByRole("button", { name: `Delete ${title}` }).click();
    await expect(page.getByText("Product deleted.", { exact: false })).toBeVisible();
}

async function deleteDiaryEntryIfPresent(page: Page, title: string) {
    const entry = diaryEntry(page, title);
    if ((await entry.count()) === 0) return;

    await acceptNextConfirmation(page);
    await entry.getByRole("button", { name: `Delete ${title}` }).click();
    await expect(entry).toHaveCount(0);
}

test.describe("personal nutrition", () => {
    test("creates, edits, logs, moves, and deletes a packaged product", async ({ page }) => {
        const title = uniqueValue("E2E frozen pizza");
        const manualTitle = uniqueValue("E2E side salad");
        const barcode = `${Date.now()}`.slice(-12);
        let productCreated = false;
        let diaryDate: string | null = null;

        try {
            await gotoHydrated(page, "/products");
            await expect(
                page.getByRole("heading", { name: "Products", exact: true })
            ).toBeVisible();

            await page.getByRole("button", { name: "Add product" }).click();
            const productDialog = page.getByRole("dialog", { name: "Review product" });
            await productDialog.getByLabel("Name").fill(title);
            await productDialog.getByLabel("Brand").fill("Playwright Foods");
            await productDialog.getByLabel("Barcode").fill(barcode);
            await productDialog.getByLabel("Values shown on label").selectOption("per_package");
            await productDialog.getByLabel("Calories").fill("720");
            await productDialog.getByLabel("Carbs (g)").fill("80");
            await productDialog.getByLabel("Fat (g)").fill("28");
            await productDialog.getByLabel("Protein (g)").fill("32");
            await productDialog.getByLabel("Package size", { exact: true }).fill("360");
            await productDialog.getByRole("button", { name: "Save product" }).click();

            productCreated = true;
            await expect(page.getByText("Product saved.", { exact: true })).toBeVisible();

            await page.getByPlaceholder("Search name, brand, or barcode…").fill(title);
            await page.getByRole("button", { name: "Search", exact: true }).click();
            await page.waitForSelector('body[data-svelte-hydrated="true"]');
            const row = productRow(page, title);
            await expect(row).toContainText("720 kcal");
            await expect(row).toContainText(barcode);

            await row.getByRole("button", { name: "Edit", exact: true }).click();
            const editProductDialog = page.getByRole("dialog", { name: "Edit product" });
            await editProductDialog.getByLabel("Calories").fill("740");
            await editProductDialog.getByRole("button", { name: "Save changes" }).click();
            await expect(page.getByText("Product updated.", { exact: true })).toBeVisible();
            await expect(productRow(page, title)).toContainText("740 kcal");

            await productRow(page, title).getByRole("link", { name: "Log", exact: true }).click();
            await expect(page).toHaveURL(/\/nutrition\?source_type=product/);
            diaryDate = await page.evaluate(() => {
                const today = new Date();
                const year = today.getFullYear();
                const month = String(today.getMonth() + 1).padStart(2, "0");
                const day = String(today.getDate()).padStart(2, "0");
                return `${year}-${month}-${day}`;
            });

            const addDialog = page.getByRole("dialog", { name: "Add food" });
            await expect(addDialog.getByRole("combobox", { name: "Saved food" })).toContainText(
                title
            );
            await expect(addDialog.getByLabel("Unit")).toHaveValue("package");
            await addDialog.getByLabel("Meal").selectOption("dinner");
            await addDialog.getByRole("button", { name: "Add to diary" }).click();

            await expect(page.getByText("Food added to the diary.", { exact: true })).toBeVisible();
            await expect(diaryEntry(page, title)).toContainText("1 package · 740 kcal");

            await page.getByRole("button", { name: "Add food" }).click();
            const manualDialog = page.getByRole("dialog", { name: "Add food" });
            await manualDialog.getByRole("button", { name: "Enter a one-off food" }).click();
            await manualDialog.getByLabel("Description").fill(manualTitle);
            await manualDialog.getByLabel("Calories").fill("110");
            await manualDialog.getByLabel("Meal").selectOption("dinner");
            await manualDialog.getByRole("button", { name: "Add to diary" }).click();
            await expect(diaryEntry(page, manualTitle)).toContainText("110 kcal");
            await expect(diaryEntry(page, manualTitle)).toContainText("Manual");

            await diaryEntry(page, title).getByRole("button", { name: "Edit" }).click();
            const editEntryDialog = page.getByRole("dialog", { name: "Edit diary entry" });
            await editEntryDialog.getByLabel("Meal").selectOption("breakfast");
            await editEntryDialog.getByLabel("Note").fill("Moved by the Playwright test");
            await editEntryDialog.getByRole("button", { name: "Save changes" }).click();
            await expect(page.getByText("Diary entry updated.", { exact: true })).toBeVisible();
            await expect(diaryEntry(page, title)).toContainText("Moved by the Playwright test");

            await deleteDiaryEntryIfPresent(page, title);
            await deleteDiaryEntryIfPresent(page, manualTitle);
            await deleteProductIfPresent(page, title);
            productCreated = false;
        } finally {
            if (diaryDate) {
                await gotoHydrated(page, `/nutrition?date=${diaryDate}`).catch(() => undefined);
                await deleteDiaryEntryIfPresent(page, title).catch(() => undefined);
                await deleteDiaryEntryIfPresent(page, manualTitle).catch(() => undefined);
            }
            if (productCreated) {
                await deleteProductIfPresent(page, title).catch(() => undefined);
            }
        }
    });

    test("reviews a barcode result before saving it", async ({ page }) => {
        const title = uniqueValue("E2E barcode yoghurt");
        const barcode = `${Date.now()}7`.slice(-13);
        let productCreated = false;

        await page.route(`**/products/barcode/${barcode}`, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify({
                    title,
                    brand: "Scanned Foods",
                    barcode,
                    image_url: null,
                    nutrition_basis: "per_100g",
                    calories: 91,
                    carbohydrates: 7.5,
                    fat: null,
                    protein: 10,
                    serving_size: 150,
                    serving_size_unit: "g",
                    package_size: 450,
                    package_size_unit: "g",
                    missing_nutrients: ["fat"],
                    needs_review: true,
                    existing_product_id: null
                })
            });
        });

        try {
            await gotoHydrated(page, "/products");
            await page.getByRole("button", { name: "Add product" }).click();
            await page
                .getByRole("dialog", { name: "Review product" })
                .getByRole("button", { name: "Scan product barcode" })
                .click();
            const scanDialog = page.getByRole("dialog", { name: "Scan a product" });
            await expect(
                scanDialog.getByRole("button", { name: "Take or choose photo" })
            ).toBeVisible();
            await scanDialog.getByPlaceholder("Enter barcode manually").fill(barcode);
            await scanDialog.getByRole("button", { name: "Look up" }).click();

            const reviewDialog = page.getByRole("dialog", { name: "Review product" });
            await expect(reviewDialog.getByText("Barcode result needs review")).toBeVisible();
            await expect(reviewDialog.getByText("Missing: fat.")).toBeVisible();
            await expect(reviewDialog.getByLabel("Name")).toHaveValue(title);
            await expect(reviewDialog.getByLabel("Calories")).toHaveValue("91");
            await expect(reviewDialog.getByLabel("Fat (g)")).toHaveValue("");
            await reviewDialog.getByRole("button", { name: "Save product" }).click();

            productCreated = true;
            await expect(page.getByText("Product saved.", { exact: true })).toBeVisible();
            await expect(productRow(page, title)).toContainText("Unknown");

            await deleteProductIfPresent(page, title);
            productCreated = false;
        } finally {
            if (productCreated) {
                await deleteProductIfPresent(page, title).catch(() => undefined);
            }
        }
    });

    test("searches recipes, products, and ingredients from one saved-food picker", async ({
        page
    }) => {
        const title = uniqueValue("E2E unified picker product");
        const date = "2099-11-04";
        let productCreated = false;

        try {
            await gotoHydrated(page, "/products");
            await page.getByRole("button", { name: "Add product" }).click();
            const productDialog = page.getByRole("dialog", { name: "Review product" });
            await productDialog.getByLabel("Name").fill(title);
            await productDialog.getByLabel("Values shown on label").selectOption("per_package");
            await productDialog.getByLabel("Calories").fill("400");
            await productDialog.getByRole("button", { name: "Save product" }).click();
            productCreated = true;
            await expect(page.getByText("Product saved.", { exact: true })).toBeVisible();

            await gotoHydrated(page, `/nutrition?date=${date}`);
            await page.getByRole("button", { name: "Add food" }).click();
            const addDialog = page.getByRole("dialog", { name: "Add food" });
            await expect(addDialog.getByLabel("Food type")).toHaveCount(0);
            await expect(addDialog.getByLabel("Amount")).toHaveCount(0);

            await addDialog.getByRole("combobox", { name: "Saved food" }).click();
            await page.getByPlaceholder("Search all saved foods…").fill(title);
            const productOption = page
                .locator('[data-slot="command-item"]')
                .filter({ hasText: `${title} · Product` });
            await expect(productOption).toHaveCount(1);
            await productOption.click();

            await expect(addDialog.getByRole("combobox", { name: "Saved food" })).toContainText(
                `${title} · Product`
            );
            await expect(addDialog.getByLabel("Amount")).toHaveValue("1");
            await expect(addDialog.getByLabel("Unit")).toHaveValue("package");
            await addDialog.getByLabel("Amount").fill("0.5");
            await addDialog.getByLabel("Meal").selectOption("snack");
            await addDialog.getByRole("button", { name: "Add to diary" }).click();

            await expect(page.getByText("Food added to the diary.", { exact: true })).toBeVisible();
            await expect(diaryEntry(page, title)).toContainText(/0[,.]5\s+package · 200 kcal/);

            await deleteDiaryEntryIfPresent(page, title);
            await deleteProductIfPresent(page, title);
            productCreated = false;
        } finally {
            await gotoHydrated(page, `/nutrition?date=${date}`).catch(() => undefined);
            await deleteDiaryEntryIfPresent(page, title).catch(() => undefined);
            if (productCreated) {
                await deleteProductIfPresent(page, title).catch(() => undefined);
            }
        }
    });

    test("corrects a quick-add draft and saves the valid batch atomically", async ({ page }) => {
        const firstTitle = uniqueValue("E2E cinnamon roll");
        const secondTitle = uniqueValue("E2E cafe snack");
        const originalDate = "2099-07-14";
        const destinationDate = "2099-07-13";

        try {
            await gotoHydrated(page, `/nutrition?date=${originalDate}`);
            await expect(page.getByRole("heading", { name: "Food diary" })).toBeVisible();

            await page.getByRole("link", { name: "Previous" }).click();
            await expect(page).toHaveURL(new RegExp(`date=${destinationDate}`));

            await page
                .getByLabel("What did you eat?")
                .fill(
                    [
                        "Aftensmad:",
                        `manual: ${firstTitle} | 321 kcal | carbs 40 g | fat ?`,
                        `manual: ${secondTitle}`
                    ].join("\n")
                );
            await page.getByRole("button", { name: "Review entries" }).click();

            await expect(page.getByRole("heading", { name: "Review before saving" })).toBeVisible();
            const editors = page.locator("[data-entry-editor]");
            await expect(editors).toHaveCount(2);
            await expect(editors.nth(0)).toContainText("321 kcal");
            await expect(editors.nth(1)).toContainText("This food needs details");
            await editors.nth(1).getByLabel("Calories").fill("42");

            const confirmBatch = page.getByRole("button", { name: "Add 2 entries" });
            await expect(confirmBatch).toBeEnabled();
            await confirmBatch.click();

            await expect(
                page.getByText("Reviewed foods added to the diary.", { exact: true })
            ).toBeVisible();
            await expect(page.getByRole("heading", { name: "Review before saving" })).toHaveCount(
                0
            );
            await expect(diaryEntry(page, firstTitle)).toContainText("321 kcal");
            await expect(diaryEntry(page, secondTitle)).toContainText("42 kcal");
            await expect(page.getByText("Incomplete", { exact: true }).first()).toBeVisible();

            await page.getByRole("link", { name: /Next/ }).click();
            await expect(page).toHaveURL(new RegExp(`date=${originalDate}`));
            await expect(diaryEntry(page, firstTitle)).toHaveCount(0);
            await expect(diaryEntry(page, secondTitle)).toHaveCount(0);
        } finally {
            for (const date of [destinationDate, originalDate]) {
                const loaded = await gotoHydrated(page, `/nutrition?date=${date}`)
                    .then(() => true)
                    .catch(() => false);
                if (!loaded) continue;
                await deleteDiaryEntryIfPresent(page, firstTitle).catch(() => undefined);
                await deleteDiaryEntryIfPresent(page, secondTitle).catch(() => undefined);
            }
        }
    });

    test("requires an amount before confirming an exact quick-add catalog match", async ({
        page
    }) => {
        const title = uniqueValue("AAA E2E missing quantity product");
        const date = "2099-08-15";
        let productCreated = false;

        try {
            await gotoHydrated(page, "/products");
            await page.getByRole("button", { name: "Add product" }).click();
            const productDialog = page.getByRole("dialog", { name: "Review product" });
            await productDialog.getByLabel("Name").fill(title);
            await productDialog.getByLabel("Calories").fill("100");
            await productDialog.getByRole("button", { name: "Save product" }).click();

            productCreated = true;
            await expect(page.getByText("Product saved.", { exact: true })).toBeVisible();

            await gotoHydrated(page, `/nutrition?date=${date}`);
            await page.getByLabel("What did you eat?").fill(`product: ${title}`);
            await page.getByRole("button", { name: "Review entries" }).click();

            const editor = page.locator("[data-entry-editor]").filter({ hasText: title });
            await expect(editor).toContainText("This food needs details");

            const confirmBatch = page.getByRole("button", { name: "Add 1 entry" });
            await expect(confirmBatch).toBeDisabled();
            await editor.getByLabel("Amount").fill("125");
            await expect(confirmBatch).toBeEnabled();
            await confirmBatch.click();

            await expect(
                page.getByText("Reviewed foods added to the diary.", { exact: true })
            ).toBeVisible();
            await expect(diaryEntry(page, title)).toContainText("125 g · 125 kcal");

            await deleteDiaryEntryIfPresent(page, title);
            await deleteProductIfPresent(page, title);
            productCreated = false;
        } finally {
            await gotoHydrated(page, `/nutrition?date=${date}`).catch(() => undefined);
            await deleteDiaryEntryIfPresent(page, title).catch(() => undefined);
            if (productCreated) {
                await deleteProductIfPresent(page, title).catch(() => undefined);
            }
        }
    });

    test("offers automatically ranked frequent entries for review and reuse", async ({ page }) => {
        const title = uniqueValue("E2E usual smoothie");
        const dates = ["2099-10-01", "2099-10-02", "2099-10-03"];

        async function logManualFood(date: string) {
            await gotoHydrated(page, `/nutrition?date=${date}`);
            await page.getByRole("button", { name: "Add food" }).click();
            const dialog = page.getByRole("dialog", { name: "Add food" });
            await dialog.getByRole("button", { name: "Enter a one-off food" }).click();
            await dialog.getByLabel("Description").fill(title);
            await dialog.getByLabel("Calories").fill("245");
            await dialog.getByLabel("Carbs (g)").fill("38");
            await dialog.getByLabel("Fat (g)").fill("6");
            await dialog.getByLabel("Protein (g)").fill("9");
            await dialog.getByLabel("Meal").selectOption("breakfast");
            await dialog.getByRole("button", { name: "Add to diary" }).click();
            await expect(page.getByText("Food added to the diary.", { exact: true })).toBeVisible();
        }

        try {
            await logManualFood(dates[0]);
            await page.getByRole("button", { name: "Add food" }).click();
            let addDialog = page.getByRole("dialog", { name: "Add food" });
            await expect(
                addDialog.getByRole("button", {
                    name: `Use frequently logged ${title}, 1 piece`
                })
            ).toHaveCount(0);
            await addDialog.getByRole("button", { name: "Cancel" }).click();

            await logManualFood(dates[1]);
            await gotoHydrated(page, `/nutrition?date=${dates[2]}`);
            await page.getByRole("button", { name: "Add food" }).click();
            addDialog = page.getByRole("dialog", { name: "Add food" });

            const frequentEntry = addDialog.getByRole("button", {
                name: `Use frequently logged ${title}, 1 piece`
            });
            await expect(
                addDialog.getByRole("heading", { name: "Frequently logged" })
            ).toBeVisible();
            await expect(frequentEntry).toContainText("1 piece · 245 kcal · 2 logs");
            const defaultMeal = await addDialog.getByLabel("Meal").inputValue();
            await frequentEntry.click();

            await expect(addDialog.getByRole("heading", { name: "Frequently logged" })).toHaveCount(
                0
            );
            await expect(addDialog.getByLabel("Description")).toHaveValue(title);
            await expect(addDialog.getByLabel("Calories")).toHaveValue("245");
            await expect(addDialog.getByLabel("Carbs (g)")).toHaveValue("38");
            await expect(addDialog.getByLabel("Fat (g)")).toHaveValue("6");
            await expect(addDialog.getByLabel("Protein (g)")).toHaveValue("9");
            await expect(addDialog.getByLabel("Meal")).toHaveValue(defaultMeal);

            await addDialog.getByRole("button", { name: "Add to diary" }).click();
            await expect(diaryEntry(page, title)).toContainText("245 kcal");
        } finally {
            for (const date of dates) {
                await gotoHydrated(page, `/nutrition?date=${date}`).catch(() => undefined);
                await deleteDiaryEntryIfPresent(page, title).catch(() => undefined);
            }
        }
    });

    test("keeps Formsnap labels and controls aligned across the new forms", async ({ page }) => {
        await gotoHydrated(page, "/nutrition?date=2099-09-01");

        const quickAdd = page.locator("form").filter({
            has: page.getByRole("button", { name: "Review entries" })
        });
        const quickText = quickAdd.getByLabel("What did you eat?");
        const defaultMeal = quickAdd.getByLabel("Default meal");
        await expectFieldStacked(quickAdd, quickText);
        await expectFieldStacked(quickAdd, defaultMeal);

        const [quickTextBox, defaultMealBox] = await Promise.all([
            quickText.boundingBox(),
            defaultMeal.boundingBox()
        ]);
        expect(quickTextBox).not.toBeNull();
        expect(defaultMealBox).not.toBeNull();
        if (quickTextBox && defaultMealBox) {
            expect(quickTextBox.width).toBeGreaterThan(defaultMealBox.width * 2);
            expect(defaultMealBox.x).toBeGreaterThan(quickTextBox.x + quickTextBox.width);
        }

        await page.getByRole("button", { name: "Add food" }).click();
        const entryDialog = page.getByRole("dialog", { name: "Add food" });
        for (const name of ["Meal", "Saved food"]) {
            await expectFieldStacked(entryDialog, entryDialog.getByLabel(name, { exact: true }));
        }
        await entryDialog.getByRole("button", { name: "Enter a one-off food" }).click();
        for (const name of ["Description", "Calories", "Carbs (g)", "Fat (g)", "Protein (g)"]) {
            await expectFieldStacked(entryDialog, entryDialog.getByLabel(name, { exact: true }));
        }
        await entryDialog.getByRole("button", { name: "Cancel" }).click();

        await gotoHydrated(page, "/products");
        await page.getByRole("button", { name: "Add product" }).click();
        const productDialog = page.getByRole("dialog", { name: "Review product" });
        for (const name of [
            "Name",
            "Brand",
            "Barcode",
            "Values shown on label",
            "Calories",
            "Carbs (g)",
            "Fat (g)",
            "Protein (g)",
            "Serving size",
            "Serving size unit",
            "Package size",
            "Package size unit"
        ]) {
            await expectFieldStacked(
                productDialog,
                productDialog.getByLabel(name, { exact: true })
            );
        }
    });
});

test.describe("personal nutrition on a 390 px viewport", () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test("shows scoped navigation and usable diary and product pages", async ({ page }) => {
        await gotoHydrated(page, "/");
        await page.getByRole("button", { name: "Open navigation" }).click();
        const navigation = page.getByRole("dialog");
        await expect(navigation.getByRole("link", { name: "Nutrition" })).toBeVisible();
        await expect(navigation.getByRole("link", { name: "Products" })).toBeVisible();

        await navigation.getByRole("link", { name: "Nutrition" }).click();
        await expect(page.getByRole("heading", { name: "Food diary" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Breakfast" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Lunch" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Dinner" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Snack" })).toBeVisible();

        const quickAdd = page.locator("form").filter({
            has: page.getByRole("button", { name: "Review entries" })
        });
        await expectFieldStacked(quickAdd, quickAdd.getByLabel("What did you eat?"));
        await expectFieldStacked(quickAdd, quickAdd.getByLabel("Default meal"));

        await page.getByRole("button", { name: "Add food" }).click();
        const addDialog = page.getByRole("dialog", { name: "Add food" });
        await expect(addDialog.getByLabel("Meal")).toBeVisible();
        await expect(addDialog.getByLabel("Saved food")).toBeVisible();
        await expectFieldStacked(addDialog, addDialog.getByLabel("Meal"));
        await expectFieldStacked(addDialog, addDialog.getByLabel("Saved food"));
        await addDialog.getByRole("button", { name: "Cancel" }).click();

        await gotoHydrated(page, "/products");
        await expect(page.getByRole("heading", { name: "Products", exact: true })).toBeVisible();
        await expect(page.getByRole("button", { name: "Scan", exact: true })).toBeVisible();
        await expect(page.getByRole("button", { name: "Add product" })).toBeVisible();
        await page.getByRole("button", { name: "Add product" }).click();
        const productDialog = page.getByRole("dialog", { name: "Review product" });
        await expectFieldStacked(productDialog, productDialog.getByLabel("Name", { exact: true }));
        await expectFieldStacked(
            productDialog,
            productDialog.getByLabel("Calories", { exact: true })
        );
        await expect
            .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
            .toBe(true);
    });
});
