import { expect, test, type Locator, type Page } from "@playwright/test";

type EditorHarness = {
    editor: Locator;
    pageErrors: string[];
};

async function openRecipeInstructionsEditor(
    page: Page,
    ingredientTitle?: string
): Promise<EditorHarness> {
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));

    if (ingredientTitle) {
        await page.addInitScript((title) => {
            if (localStorage.getItem("recipe-snapshot-/recipes/create")) return;
            localStorage.setItem(
                "recipe-snapshot-/recipes/create",
                JSON.stringify({
                    ingredients: [
                        { id: "instruction-ingredient-test", title, amount: 200, unit: "g" }
                    ]
                })
            );
        }, ingredientTitle);
    }
    await page.goto("/recipes/create");
    await page.waitForSelector('body[data-svelte-hydrated="true"]');

    const editor = page.locator(".tiptap.ProseMirror");
    await expect(editor).toBeVisible();
    await editor.fill("");

    return { editor, pageErrors };
}

function expectNoPageErrors(pageErrors: string[]) {
    expect(pageErrors, "the instructions editor should not raise browser errors").toEqual([]);
}

test.describe("recipe instructions editor", () => {
    test("binds typed ingredient amounts and lets the author edit their portion", async ({
        page
    }) => {
        const { editor, pageErrors } = await openRecipeInstructionsEditor(page, "Butter");
        await editor.pressSequentially("Brown the meat in {butter:25%}.");
        const reference = editor.locator("[data-ingredient-amount]");
        await expect(reference).toHaveText("{Butter:25%}");
        await reference.click();
        const dialog = page.getByRole("dialog", { name: "Ingredient amount", exact: true });
        await expect(dialog.getByRole("status")).toHaveText(
            "At the recipe's original servings: 50 g"
        );
        await dialog.getByLabel("Portion", { exact: true }).fill("1/2");
        await expect(dialog.getByRole("status")).toHaveText(
            "At the recipe's original servings: 100 g"
        );
        await dialog.getByRole("button", { name: "Insert amount", exact: true }).click();
        await expect(reference).toHaveText("{Butter:1/2}");
        await expect(page.locator('input[name="instructions"]')).toHaveValue(
            /data-ingredient-amount/
        );
        await page.reload();
        await expect(reference).toHaveText("{Butter:1/2}");
        expectNoPageErrors(pageErrors);
    });

    test("supports any ingredient and leaves invalid tokens as text", async ({ page }) => {
        const { editor, pageErrors } = await openRecipeInstructionsEditor(page, "Smoked paprika");
        await editor.pressSequentially("Add {Smoked paprika:1/4}");
        await editor.locator("[data-ingredient-amount]").click();
        const dialog = page.getByRole("dialog", { name: "Ingredient amount", exact: true });
        await dialog.getByLabel("Portion", { exact: true }).fill("1/4");
        await expect(dialog.getByRole("status")).toHaveText(
            "At the recipe's original servings: 50 g"
        );
        await dialog.getByRole("button", { name: "Insert amount", exact: true }).click();
        await expect(editor.locator("[data-ingredient-amount]")).toHaveText("{Smoked paprika:1/4}");
        await editor.press("End");
        await editor.pressSequentially(" {Smoked paprika:1/0} {Unknown:25%}");
        await expect(editor.locator("[data-ingredient-amount]")).toHaveCount(1);
        await expect(editor).toContainText("{Smoked paprika:1/0} {Unknown:25%}");
        await editor.evaluate((element) => {
            const clipboardData = new DataTransfer();
            clipboardData.setData("text/plain", " {Smoked paprika:50%}");
            element.dispatchEvent(new ClipboardEvent("paste", { clipboardData, bubbles: true }));
        });
        await expect(editor.locator("[data-ingredient-amount]")).toHaveCount(2);
        expectNoPageErrors(pageErrors);
    });

    test("creates and continues a bullet list from the Markdown shortcut", async ({ page }) => {
        const { editor, pageErrors } = await openRecipeInstructionsEditor(page);

        await editor.pressSequentially("- ");
        await expect(editor.locator("ul > li")).toHaveCount(1);

        await editor.pressSequentially("First bullet");
        await editor.press("Enter");
        await editor.pressSequentially("Second bullet");

        const items = editor.locator("ul > li");
        await expect(items).toHaveCount(2);
        await expect(items.nth(0)).toHaveText("First bullet");
        await expect(items.nth(1)).toHaveText("Second bullet");
        expectNoPageErrors(pageErrors);
    });

    test("creates and continues an ordered list from the Markdown shortcut", async ({ page }) => {
        const { editor, pageErrors } = await openRecipeInstructionsEditor(page);

        await editor.pressSequentially("1. ");
        await expect(editor.locator("ol > li")).toHaveCount(1);

        await editor.pressSequentially("First numbered item");
        await editor.press("Enter");
        await editor.pressSequentially("Second numbered item");

        const items = editor.locator("ol > li");
        await expect(items).toHaveCount(2);
        await expect(items.nth(0)).toHaveText("First numbered item");
        await expect(items.nth(1)).toHaveText("Second numbered item");
        expectNoPageErrors(pageErrors);
    });

    test("toggles bold formatting with the keyboard shortcut", async ({ page }) => {
        const { editor, pageErrors } = await openRecipeInstructionsEditor(page);

        await editor.press("ControlOrMeta+B");
        await editor.pressSequentially("Bold text");
        await editor.press("ControlOrMeta+B");
        await editor.pressSequentially(" plain text");

        await expect(editor.locator("p > strong")).toHaveText("Bold text");
        await expect(editor.locator("p")).toHaveText("Bold text plain text");
        await expect
            .poll(() => editor.innerHTML())
            .toBe("<p><strong>Bold text</strong> plain text</p>");
        expectNoPageErrors(pageErrors);
    });
});
