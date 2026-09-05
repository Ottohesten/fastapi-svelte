import { expect, test, type Locator, type Page } from "@playwright/test";

type EditorHarness = {
    editor: Locator;
    pageErrors: string[];
};

async function openRecipeInstructionsEditor(page: Page): Promise<EditorHarness> {
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));

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
