import { test as base } from "@playwright/test";
import { GamesPage } from "../pages/games-page";

export const test = base.extend<{ gamesPage: GamesPage }, { cleanupGames: void }>({
    gamesPage: async ({ page }, use) => {
        const gamesPage = new GamesPage(page);
        await gamesPage.goto();
        await page.waitForSelector('body[data-svelte-hydrated="true"]');
        await gamesPage.createNewGame({
            title: `Playwright Session 1`,
            teamNames: ["Red Team", "Blue Team"]
        });
        // await gamesPage.createNewGame({
        //     title: `Playwright Session 2`,
        //     teamNames: ["Red Team", "Blue Team"]
        // });
        await use(gamesPage);

        // teardown
    }
});

export { expect } from "@playwright/test";
