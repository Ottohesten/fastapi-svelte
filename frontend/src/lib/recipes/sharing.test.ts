import { describe, expect, test } from "bun:test";
import { ingredientListText, parseServings, scaledRecipeUrl } from "./sharing";

describe("recipe sharing", () => {
    test("reads positive whole and fractional serving counts", () => {
        expect(parseServings("12", 4)).toBe(12);
        expect(parseServings("2.5", 4)).toBe(2.5);
    });

    test("falls back for missing, empty, invalid, and non-positive servings", () => {
        for (const value of [null, "", " ", "invalid", "0", "-2", "NaN", "Infinity", "1e999"]) {
            expect(parseServings(value, 4)).toBe(4);
        }
    });

    test("preserves other query parameters and fragments when sharing", () => {
        const original = new URL(
            "https://example.com/recipes/soup?servings=4&source=menu#ingredients"
        );
        const shared = scaledRecipeUrl(original, 12);
        expect(shared.searchParams.getAll("servings")).toEqual(["12"]);
        expect(shared.searchParams.get("source")).toBe("menu");
        expect(shared.hash).toBe("#ingredients");
        expect(original.searchParams.get("servings")).toBe("4");
    });

    test("exports required quantities with units and readable rounding", () => {
        const potatoes = { title: "Potatoes", amount: 1500, unit: "g", consumed_amount: 1200 };
        expect(
            ingredientListText("Soup", 12, [
                potatoes,
                { title: "Olive oil", amount: 1.333333333, unit: "tbsp" },
                { title: "Bay leaves", amount: 3, unit: "" }
            ])
        ).toBe("Soup\n12 servings\n\n- 1500 g Potatoes\n- 1.33 tbsp Olive oil\n- 3 Bay leaves");
    });

    test("handles a single serving and an empty list", () => {
        expect(ingredientListText("Soup", 1, [])).toBe("Soup\n1 serving\n");
    });
});
