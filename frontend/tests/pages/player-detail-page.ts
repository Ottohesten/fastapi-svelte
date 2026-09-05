import { expect, type Locator, type Page } from "@playwright/test";

export class PlayerDetailPage {
    readonly page: Page;
    readonly heading: Locator;
    readonly updatePlayerButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.heading = page.getByRole("heading", { level: 1 });
        this.updatePlayerButton = page.getByRole("button", { name: "Update player" });
    }

    async expectLoaded(playerName: string) {
        await expect(this.heading).toHaveText(playerName);
        await expect(this.page).toHaveURL(/\/game\/[^/]+\/player\/[^/]+$/);
    }

    async selectTeam(teamName: string) {
        await this.page.getByLabel("Team", { exact: true }).click();
        await this.page.getByRole("option", { name: teamName, exact: true }).click();
    }

    async expectTeam(teamName: string) {
        await expect(this.page.getByText(teamName, { exact: true }).first()).toBeVisible();
    }

    async hasAvailableDrinks() {
        return (await this.page.locator('input[id^="drink-checkbox-"]').count()) > 0;
    }

    async selectFirstDrinkWithAmount(amount: number) {
        const checkbox = this.page.locator('input[id^="drink-checkbox-"]').first();
        await expect(checkbox).toBeVisible();
        const drinkId = await this.drinkIdFromCheckbox(checkbox);

        if (!(await checkbox.isChecked())) {
            await checkbox.check();
        }
        await this.page.locator(`#drink-amount-${drinkId}`).fill(String(amount));
        return drinkId;
    }

    async unselectDrink(drinkId: string) {
        const checkbox = this.page.locator(`#drink-checkbox-${drinkId}`);
        await expect(checkbox).toBeVisible();
        if (await checkbox.isChecked()) {
            await checkbox.uncheck();
        }
    }

    async submitAndReopen() {
        const currentUrl = this.page.url();
        const currentPath = new URL(currentUrl).pathname;

        await Promise.all([
            this.page.waitForResponse(
                (response) =>
                    response.request().method() === "POST" &&
                    new URL(response.url()).pathname === currentPath
            ),
            this.updatePlayerButton.click()
        ]);

        // Reopen from the server so assertions verify persisted state, not the local form store.
        await this.page.goto(currentUrl);
    }

    async expectDrinkSelectedWithAmount(drinkId: string, amount: number) {
        const checkbox = this.page.locator(`#drink-checkbox-${drinkId}`);
        await expect(checkbox).toBeChecked();
        await expect(this.page.locator(`#drink-amount-${drinkId}`)).toHaveValue(String(amount));
    }

    async expectDrinkNotSelected(drinkId: string) {
        const checkbox = this.page.locator(`#drink-checkbox-${drinkId}`);
        await expect(checkbox).not.toBeChecked();
    }

    private async drinkIdFromCheckbox(checkbox: Locator) {
        const id = await checkbox.getAttribute("id");
        if (!id || !id.startsWith("drink-checkbox-")) {
            throw new Error("Could not resolve drink id from checkbox");
        }
        return id.replace("drink-checkbox-", "");
    }
}
