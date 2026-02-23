import { expect, type Locator, type Page } from "@playwright/test";
import type { PlayerSeed } from "../utils/random";

export class GameEditPage {
    readonly page: Page;
    readonly gameManagementHeading: Locator;
    readonly playerNameInput: Locator;
    readonly playerTeamSelect: Locator;
    readonly addPlayerButton: Locator;
    readonly teamNameInput: Locator;
    readonly addTeamButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.gameManagementHeading = page.getByRole("heading", { name: "Game Management" });
        this.playerNameInput = page.getByLabel("Player Name");
        this.playerTeamSelect = page.getByLabel("Team (Optional)");
        this.addPlayerButton = page.getByRole("button", { name: "Add Player" });
        this.teamNameInput = page.getByLabel("Team Name");
        this.addTeamButton = page.getByRole("button", { name: "Add Team" });
    }

    async expectLoaded() {
        await expect(this.gameManagementHeading).toBeVisible();
        await expect(this.page).toHaveURL(/\/game\/[^/]+\/update$/);
    }

    async addPlayer(player: PlayerSeed) {
        await this.playerNameInput.fill(player.name);
        await this.playerTeamSelect.click();
        await this.page.getByRole("option", { name: player.teamName, exact: true }).click();
        await this.addPlayerButton.click();
        await expect(this.page.getByText(player.name, { exact: true })).toBeVisible();
    }

    async addPlayerWithoutTeam(playerName: string) {
        await this.playerNameInput.fill(playerName);
        await this.addPlayerButton.click();
        await expect(this.playerCard(playerName)).toBeVisible();
    }

    async addPlayerToTeam(playerName: string, teamName: string) {
        await this.addPlayer({ name: playerName, teamName });
    }

    async addPlayers(players: PlayerSeed[]) {
        for (const player of players) {
            await this.addPlayer(player);
        }
    }

    async addTeam(teamName: string) {
        await this.teamNameInput.fill(teamName);
        await this.addTeamButton.click();
        await expect(this.teamCard(teamName)).toBeVisible();
    }

    async deleteTeam(teamName: string) {
        await this.teamCard(teamName).getByRole("button", { name: "Delete" }).click();
        await expect(this.teamCard(teamName)).toHaveCount(0);
    }

    async deletePlayer(playerName: string) {
        await this.playerCard(playerName).getByRole("button", { name: "Delete" }).click();
        await expect(this.playerCard(playerName)).toHaveCount(0);
    }

    async expectTeamVisible(teamName: string) {
        await expect(this.teamCard(teamName)).toBeVisible();
    }

    async expectPlayerVisible(playerName: string) {
        await expect(this.playerCard(playerName)).toBeVisible();
    }

    async expectPlayerWithoutTeam(playerName: string) {
        await expect(
            this.playerCard(playerName).getByText("No team assigned", { exact: false })
        ).toBeVisible();
    }

    async expectPlayerInTeam(playerName: string, teamName: string) {
        await expect(this.playerCard(playerName)).toContainText(
            new RegExp(`Team:\\s*${escapeForRegex(teamName)}`)
        );
    }

    async expectPlayerNotInTeam(playerName: string, teamName: string) {
        const card = this.playerCard(playerName);
        if ((await card.count()) === 0) {
            return;
        }
        await expect(card).not.toContainText(new RegExp(`Team:\\s*${escapeForRegex(teamName)}`));
    }

    async openPlayerDetails(playerName: string) {
        await this.playerCard(playerName).locator("a").first().click();
        await expect(this.page).toHaveURL(/\/game\/[^/]+\/player\/[^/]+$/);
    }

    async gotoDashboard() {
        await this.page.goto(this.page.url().replace(/\/update$/, ""));
        await expect(this.page).toHaveURL(/\/game\/[^/]+$/);
    }

    private teamCard(teamName: string) {
        return this.page
            .getByRole("heading", { name: teamName, exact: true })
            .locator("xpath=ancestor::div[contains(@class, 'surface-2')][1]");
    }

    private playerCard(playerName: string) {
        return this.page
            .getByRole("heading", { name: playerName, exact: true })
            .locator("xpath=ancestor::div[contains(@class, 'surface-2')][1]");
    }
}

function escapeForRegex(value: string) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
