import { test, expect } from "@playwright/test";
import { GamesPage } from "./pages/games-page";

test.describe("Games page", () => {
    test("shows the games list", async ({ page }) => {
        const gamesPage = new GamesPage(page);
        await gamesPage.goto();

        await expect(page.getByRole("heading", { name: "Game sessions:" })).toBeVisible();
    });

    test("can create a new game session", async ({ page }) => {
        const gamesPage = new GamesPage(page);
        await gamesPage.goto();

        const title = `Playwright Session ${Date.now()}`;
        await gamesPage.createNewGame({
            title,
            teamNames: ["Red Team", "Blue Team"]
        });

        await expect(page.getByRole("heading", { name: title })).toBeVisible();
    });
});
