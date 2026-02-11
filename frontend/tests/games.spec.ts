import { test, expect } from "./fixtures/gamesFixture";

test.describe("Games page", () => {
    test("shows the games list", async ({ gamesPage, page }) => {
        await expect(page.getByRole("heading", { name: "Game sessions:" })).toBeVisible();
    });

    test("can create a new game session", async ({ gamesPage, page }) => {
        await page.locator("body").click();

        const title = `Playwright Session ${Date.now()}`;
        await gamesPage.createNewGame({
            title,
            teamNames: ["Red Team", "Blue Team"]
        });

        await expect(page.getByRole("heading", { name: title })).toBeVisible();
    });

    test("can delete a game session", async ({ gamesPage, page }) => {
        const title = `Playwright Session to Delete ${Date.now()}`;
        await gamesPage.createNewGame({
            title,
            teamNames: ["Red Team", "Blue Team"]
        });
        await expect(page.getByRole("heading", { name: title })).toBeVisible();

        await gamesPage.deleteGame(title);
    });
});
