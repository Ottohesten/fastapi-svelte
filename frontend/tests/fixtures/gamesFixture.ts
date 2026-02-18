import { test as base } from "@playwright/test";
import { GamesPage } from "../pages/games-page";
import { GamePage } from "../pages/game-page";
import { GameEditPage } from "../pages/game-edit-page";
import { randomPlayersForTeams, randomSessionTitle } from "../utils/random";

const defaultTeamNames = ["Red Team", "Blue Team"];

export const test = base.extend<{ gamesPage: GamesPage; gamePage: GamePage; sessionTitle: string }>({
    sessionTitle: async ({}, use) => {
        await use(randomSessionTitle());
    },
    gamesPage: async ({ page, sessionTitle }, use) => {
        const gamesPage = new GamesPage(page);
        await gamesPage.goto();
        await page.waitForSelector('body[data-svelte-hydrated="true"]');
        await gamesPage.createNewGame({
            title: sessionTitle,
            teamNames: defaultTeamNames
        });
        await use(gamesPage);

        // teardown
        await gamesPage.deleteGame(sessionTitle);
        // await gamesPage.deleteAll();
        
    },
    gamePage: async ({ gamesPage, page, sessionTitle }, use) => {
        await gamesPage.openGame(sessionTitle);
        // await page.waitForSelector('body[data-svelte-hydrated="true"]');
        const gamePage = new GamePage(page);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        await gameEditPage.expectLoaded();
        await gameEditPage.addPlayers(randomPlayersForTeams(defaultTeamNames, 2));
        await gameEditPage.gotoDashboard();
        await gamePage.expectLoaded(sessionTitle);
        await use(gamePage);
    }
});

export { expect } from "@playwright/test";
