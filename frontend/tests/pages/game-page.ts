import { expect, type Locator, type Page } from "@playwright/test";

// Page Object model for an individual game session page (e.g. /game/uuid)
export class GamePage {
    readonly page: Page;
    readonly dashboardHeading: Locator;
    readonly addDrinkToPlayerButton: Locator;
    readonly addDrinkDialogTitle: Locator;
    readonly editButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.dashboardHeading = page.getByRole("heading", { name: "Game Session Dashboard" });
        this.addDrinkToPlayerButton = page.getByText("Add Drink to Player", { exact: true });
        this.addDrinkDialogTitle = page.getByText("Add New Drink", { exact: true });
        this.editButton = page.getByRole("link", { name: "Edit" });
    }

    async goto(gameId: string) {
        await this.page.goto(`/game/${gameId}`);
    }

    async expectLoaded(title: string) {
        await expect(this.dashboardHeading).toBeVisible();
        await expect(this.page.getByText(`Session: ${title}`, { exact: false })).toBeVisible();
    }

    async openAddDrinkDialog() {
        await this.page.waitForSelector('body[data-svelte-hydrated="true"]');
        await this.addDrinkToPlayerButton.click();
        await expect(this.addDrinkDialogTitle).toBeVisible();
    }

    async expectAddDrinkFormVisible() {
        await expect(this.page.getByText("Player", { exact: true })).toBeVisible();
        await expect(this.page.getByText("Drink", { exact: true })).toBeVisible();
        await expect(this.page.getByLabel("Amount")).toBeVisible();
        await expect(this.page.getByRole('button', { name: 'Add Drink', exact: true })).toBeVisible();
    }

    async gotoEditPage() {
        await this.editButton.click();
        await expect(this.page).toHaveURL(/\/game\/[^/]+\/update$/);
    }
}
