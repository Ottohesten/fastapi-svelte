import { test, expect } from "./fixtures/gamesFixture";
import { GameEditPage } from "./pages/game-edit-page";
import { PlayerDetailPage } from "./pages/player-detail-page";
import { randomPlayerName, randomTeamName } from "./utils/random";

test.describe("Game detail page", () => {
    test("loads dashboard", async ({ gamePage, sessionTitle }) => {
        await gamePage.expectLoaded(sessionTitle);
    });

    test("opens add drink dialog with form fields", async ({ gamePage, sessionTitle }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.openAddDrinkDialog();
        await gamePage.expectAddDrinkFormVisible();
    });


    test("navigates to edit page from detail page", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        await expect(page.getByRole("heading", { name: "Game Management" })).toBeVisible();
    });
});


test.describe("Game edit page", () => {
    test("loads edit page for a specific session", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        // const gameEditPage = new GameEditPage(page);
        // await gameEditPage.expectLoaded();
    });

    test("can add team", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const teamName = randomTeamName();

        await gameEditPage.addTeam(teamName);
        await gameEditPage.expectTeamVisible(teamName);
    });

    test("can add player with no team", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const playerName = randomPlayerName();

        await gameEditPage.addPlayerWithoutTeam(playerName);
        await gameEditPage.expectPlayerVisible(playerName);
        await gameEditPage.expectPlayerWithoutTeam(playerName);
    });

    test("can add player with team", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const playerName = randomPlayerName();

        await gameEditPage.addPlayerToTeam(playerName, "Red Team");
        await gameEditPage.expectPlayerVisible(playerName);
        await gameEditPage.expectPlayerInTeam(playerName, "Red Team");
    });

    test("can delete team", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const teamName = randomTeamName();

        await gameEditPage.addTeam(teamName);
        await gameEditPage.deleteTeam(teamName);
    });

    test("can delete player", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const playerName = randomPlayerName();

        await gameEditPage.addPlayerWithoutTeam(playerName);
        await gameEditPage.deletePlayer(playerName);
    });

    test("can delete a team that has players attributed to it", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const teamName = randomTeamName();
        const firstPlayer = randomPlayerName();
        const secondPlayer = randomPlayerName();

        await gameEditPage.addTeam(teamName);
        await gameEditPage.addPlayerToTeam(firstPlayer, teamName);
        await gameEditPage.addPlayerToTeam(secondPlayer, teamName);
        await gameEditPage.deleteTeam(teamName);

        await gameEditPage.expectPlayerNotInTeam(firstPlayer, teamName);
        await gameEditPage.expectPlayerNotInTeam(secondPlayer, teamName);
    });
});

test.describe("Player detail page", () => {
    test("can add drinks to a specific player", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const playerName = randomPlayerName();

        await gameEditPage.addPlayerWithoutTeam(playerName);
        await gameEditPage.openPlayerDetails(playerName);

        const playerDetailPage = new PlayerDetailPage(page);
        await playerDetailPage.expectLoaded(playerName);
        test.skip(!(await playerDetailPage.hasAvailableDrinks()), "No drinks available in test environment.");

        const drinkId = await playerDetailPage.selectFirstDrinkWithAmount(3);
        await playerDetailPage.submitAndReopen();
        await playerDetailPage.expectLoaded(playerName);
        await playerDetailPage.expectDrinkSelectedWithAmount(drinkId, 3);
    });

    test("can remove drinks from a specific player", async ({ gamePage, sessionTitle, page }) => {
        await gamePage.expectLoaded(sessionTitle);
        await gamePage.gotoEditPage();
        const gameEditPage = new GameEditPage(page);
        const playerName = randomPlayerName();

        await gameEditPage.addPlayerWithoutTeam(playerName);
        await gameEditPage.openPlayerDetails(playerName);

        const playerDetailPage = new PlayerDetailPage(page);
        await playerDetailPage.expectLoaded(playerName);
        test.skip(!(await playerDetailPage.hasAvailableDrinks()), "No drinks available in test environment.");

        const drinkId = await playerDetailPage.selectFirstDrinkWithAmount(2);
        await playerDetailPage.submitAndReopen();
        await playerDetailPage.expectLoaded(playerName);
        await playerDetailPage.expectDrinkSelectedWithAmount(drinkId, 2);

        await playerDetailPage.unselectDrink(drinkId);
        await playerDetailPage.submitAndReopen();
        await playerDetailPage.expectLoaded(playerName);
        await playerDetailPage.expectDrinkNotSelected(drinkId);
    });
});
