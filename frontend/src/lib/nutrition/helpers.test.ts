import { describe, expect, test } from "bun:test";
import { catalogSearchScore } from "$lib/nutrition/helpers";

describe("catalogSearchScore", () => {
    test("rejects loose character-order matches", () => {
        expect(catalogSearchScore("Flæskesteg with potatoes · Recipe", "banana")).toBe(0);
        expect(catalogSearchScore("Mukimame beans · Ingredient", "banana")).toBe(0);
    });

    test("matches names, brands, barcodes, and food types by substring", () => {
        expect(catalogSearchScore("Banana · Ingredient", "banana")).toBeGreaterThan(0);
        expect(
            catalogSearchScore("Frozen fruit · Product", "smoothieco", [
                "Frozen fruit",
                "SmoothieCo",
                "5712345678901",
                "product"
            ])
        ).toBeGreaterThan(0);
        expect(
            catalogSearchScore("Frozen fruit · Product", "571234", ["5712345678901"])
        ).toBeGreaterThan(0);
        expect(
            catalogSearchScore("Banana yoghurt shake · Recipe", "banana recipe", [
                "Banana yoghurt shake",
                "recipe"
            ])
        ).toBeGreaterThan(0);
    });

    test("treats common Danish character variants as equivalent", () => {
        expect(catalogSearchScore("Flæskesteg · Recipe", "flaeskesteg")).toBeGreaterThan(0);
        expect(catalogSearchScore("Rødgrød · Recipe", "rodgrod")).toBeGreaterThan(0);
        expect(catalogSearchScore("Ål · Ingredient", "aal")).toBeGreaterThan(0);
    });
});
