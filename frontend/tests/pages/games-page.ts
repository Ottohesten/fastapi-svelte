import { expect, type Locator, type Page } from "@playwright/test";

// Page Object Model for the Games Page (this means not an individual game session page, but instead the page where you can see all the different sessions and create new ones)
export class GamesPage {
    readonly page: Page;
    readonly createGameButton: Locator;
    readonly titleInput: Locator;
    readonly addTeamButton: Locator;
    readonly submitButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.createGameButton = page.getByRole("link", { name: "Create Session" });
        this.titleInput = page.getByLabel("Title");
        this.addTeamButton = page.getByRole("button", { name: "Add Team" });
        this.submitButton = page.getByRole("button", { name: "Submit" });
    }
    async goto() {
        await this.page.goto("/game");
    }

    async createNewGame({ title, teamNames }: { title: string; teamNames: string[] }) {
        await this.createGameButton.click();

        // we get taken to to a new page /game/create
        await expect(this.page).toHaveURL("/game/create");

        // wait for hydration
        await this.page.waitForSelector('body[data-svelte-hydrated="true"]');

        // fill in the title
        await this.titleInput.fill(title);

        const teamNameInputs = this.page.getByLabel("Team Name");

        for (let i = 0; i < teamNames.length; i += 1) {
            const currentCount = await teamNameInputs.count();
            if (i >= currentCount) {
                await this.addTeamButton.click();
                await expect(teamNameInputs).toHaveCount(i + 1);
            }
            await teamNameInputs.nth(i).fill(teamNames[i] ?? `Team ${i + 1}`);
        }

        await this.submitButton.click();

        // after submit, we should be back on the game list
        await expect(this.page).toHaveURL("/game");
    }

    async deleteGame(title: string) {
        await this.goto();
        await this.page.waitForSelector('body[data-svelte-hydrated="true"]');

        const slug = String(title)
            .trim()
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9-]/g, "")
            .replace(/-+/g, "-")
            .replace(/^-|-$/g, "");
        const deleteButton = this.page.locator(`id=delete-session-${slug}`);

        if ((await deleteButton.count()) === 0) {
            return;
        }

        this.page.once("dialog", async (dialog) => {
            await dialog.accept();
        });
        await deleteButton.click();
        await expect(deleteButton).toHaveCount(0);
    }

    async deleteAll() {
        await this.goto();
        await this.page.waitForSelector('body[data-svelte-hydrated="true"]');
        const deleteButtons = this.page.getByRole("button", { name: "Delete" });

        while ((await deleteButtons.count()) > 0) {
            const currentCount = await deleteButtons.count();
            this.page.once("dialog", async (dialog) => {
                await dialog.accept();
            });
            await deleteButtons.first().click();
            await expect(deleteButtons).toHaveCount(currentCount - 1);
        }
    }
    async openGame(title: string) {
        await this.page.getByRole("heading", { name: title }).click();
        await expect(this.page).toHaveURL(/\/game\/[^/]+$/);
    }
}
