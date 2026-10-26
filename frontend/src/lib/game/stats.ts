import type { GamePlayerPublic } from "$lib/client/types.gen";

type PlayerWithDrinks = Pick<GamePlayerPublic, "drink_links">;

export type DrinkSummary = {
    id: string;
    name: string;
    amount: number;
};

export function getPlayerDrinkTotal(player: PlayerWithDrinks): number {
    return player.drink_links.reduce((total, link) => total + link.amount, 0);
}

export function summarizeDrinks(players: readonly PlayerWithDrinks[]): DrinkSummary[] {
    const totals = new Map<string, DrinkSummary>();

    for (const player of players) {
        for (const link of player.drink_links) {
            const current = totals.get(link.drink.id);
            if (current) {
                current.amount += link.amount;
            } else {
                totals.set(link.drink.id, {
                    id: link.drink.id,
                    name: link.drink.name,
                    amount: link.amount
                });
            }
        }
    }

    return [...totals.values()].sort(
        (left, right) => right.amount - left.amount || left.name.localeCompare(right.name)
    );
}

export function rankPlayersByDrinks<T extends PlayerWithDrinks>(players: readonly T[]): T[] {
    return [...players].sort(
        (left, right) => getPlayerDrinkTotal(right) - getPlayerDrinkTotal(left)
    );
}
