import { describe, expect, test } from "bun:test";
import type { GamePlayerPublic } from "$lib/client/types.gen";
import { getPlayerDrinkTotal, rankPlayersByDrinks, summarizeDrinks } from "./stats";

type TestPlayer = Pick<GamePlayerPublic, "name" | "drink_links">;

const player = (
    name: string,
    drinks: Array<{ id: string; name: string; amount: number }>
): TestPlayer => ({
    name,
    drink_links: drinks.map(({ id, name: drinkName, amount }) => ({
        amount,
        drink: { id, name: drinkName }
    }))
});

describe("game statistics", () => {
    test("totals a player's drinks", () => {
        expect(
            getPlayerDrinkTotal(
                player("Ada", [
                    { id: "water", name: "Water", amount: 2 },
                    { id: "juice", name: "Juice", amount: 3 }
                ])
            )
        ).toBe(5);
    });

    test("combines and ranks a team's drink totals", () => {
        const summary = summarizeDrinks([
            player("Ada", [
                { id: "water", name: "Water", amount: 2 },
                { id: "juice", name: "Juice", amount: 1 }
            ]),
            player("Grace", [
                { id: "water", name: "Water", amount: 3 },
                { id: "soda", name: "Soda", amount: 2 }
            ])
        ]);

        expect(summary).toEqual([
            { id: "water", name: "Water", amount: 5 },
            { id: "soda", name: "Soda", amount: 2 },
            { id: "juice", name: "Juice", amount: 1 }
        ]);
    });

    test("returns a ranked copy without mutating the roster", () => {
        const roster = [
            player("Ada", [{ id: "water", name: "Water", amount: 1 }]),
            player("Grace", [{ id: "water", name: "Water", amount: 4 }])
        ];

        expect(rankPlayersByDrinks(roster).map(({ name }) => name)).toEqual(["Grace", "Ada"]);
        expect(roster.map(({ name }) => name)).toEqual(["Ada", "Grace"]);
    });
});
