import { describe, expect, test } from "bun:test";
import {
    decodeAmountReference,
    encodeAmountReference,
    formAmountRecipe,
    ingredientReferenceFromToken,
    parseIngredientPortion,
    renderIngredientAmounts,
    resolveIngredientAmount,
    scopeImportedIngredientAmounts,
    type AmountRecipe,
    type IngredientAmountReference
} from "./ingredient-amounts";

const butter = { ingredient_id: "butter", title: "Butter", amount: 200, unit: "g" };
const root: AmountRecipe = { id: "lasagna", total_ingredients: [butter] };
const reference: IngredientAmountReference = {
    ingredientId: "butter",
    title: "Butter",
    unit: "g",
    portion: "25%",
    path: []
};
const html = (ref = reference) =>
    `<ol><li>Use <span data-ingredient-amount="${encodeAmountReference(ref)}">{Butter:25%}</span>.</li></ol>`;

describe("instruction ingredient amounts", () => {
    test("accepts percentages and fractions without evaluating expressions", () => {
        expect(parseIngredientPortion("25%")!).toBe(0.25);
        expect(parseIngredientPortion("12.5 %")!).toBe(0.125);
        expect(parseIngredientPortion("1 / 3")!).toBeCloseTo(1 / 3);
        expect(parseIngredientPortion("100%")!).toBe(1);
        for (const invalid of [
            "",
            "0%",
            "101%",
            "-25%",
            "1/0",
            "2/1",
            "Infinity%",
            "1+1",
            "alert(1)"
        ]) {
            expect(parseIngredientPortion(invalid)).toBeNull();
        }
    });

    test("binds arbitrary ingredient names to stable IDs and rejects ambiguity", () => {
        expect(ingredientReferenceFromToken("{butter:1/2}", [butter])?.ingredientId).toBe("butter");
        const paprika = { ...butter, ingredient_id: "paprika", title: "Smoked paprika" };
        expect(ingredientReferenceFromToken("{Smoked paprika:25%}", [paprika])?.ingredientId).toBe(
            "paprika"
        );
        expect(ingredientReferenceFromToken("{Missing:25%}", [butter])).toBeNull();
        expect(ingredientReferenceFromToken("{Butter:1/0}", [butter])).toBeNull();
        const alternatives = [butter, { ...butter, unit: "pcs" }];
        expect(ingredientReferenceFromToken("{Butter:25%}", alternatives)).toBeNull();
        expect(ingredientReferenceFromToken("{Butter [g]:25%}", alternatives)?.unit).toBe("g");
    });

    test("uses current required quantities and serving scale after ingredient renames", () => {
        expect(resolveIngredientAmount(reference, root, [])).toBe("50 g");
        expect(resolveIngredientAmount(reference, root, [], 2)).toBe("100 g");
        const renamed = {
            ...root,
            total_ingredients: [{ ...butter, title: "Salted butter", amount: 300 }]
        };
        expect(resolveIngredientAmount(reference, renamed, [])).toBe("75 g");
        expect(resolveIngredientAmount({ ...reference, portion: "1/3" }, root, [])).toBe("66.67 g");
    });

    test("normalizes and aggregates ingredients from form inputs and linked recipes", () => {
        const sauce = { id: "sauce", total_ingredients: [{ ...butter, amount: 50 }] };
        const combined = formAmountRecipe(
            [{ id: "butter", title: "Butter", amount: 0.1, unit: "kg" }],
            [{ id: "sauce", scale_factor: 2 }],
            [sauce]
        );
        expect(combined.total_ingredients).toEqual([butter]);
        expect(resolveIngredientAmount(reference, combined, [sauce])).toBe("50 g");
    });

    test("retains nested sub-recipe allocations and applies each link scale once", () => {
        const sauce = formAmountRecipe([], [{ id: "roux", scale_factor: 3 }], []);
        sauce.id = "sauce";
        const roux = { id: "roux", total_ingredients: [{ ...butter, amount: 40 }] };
        const parent = formAmountRecipe([], [{ id: "sauce", scale_factor: 2 }], []);
        const imported = scopeImportedIngredientAmounts(
            scopeImportedIngredientAmounts(html(), "roux"),
            "sauce"
        );
        expect(renderIngredientAmounts(imported, parent, [sauce, roux], 2)).toBe(
            "<ol><li>Use <span>120 g</span>.</li></ol>"
        );
        // A removed link must never fall back to the parent's full butter amount.
        expect(renderIngredientAmounts(imported, root, [sauce, roux])).toContain(
            "ingredient unavailable"
        );
    });

    test("renders on the server without changing surrounding rich text", () => {
        expect(
            renderIngredientAmounts(html().replace("</span>.", "</span> cold butter."), root, [])
        ).toBe("<ol><li>Use <span>50 g</span> cold butter.</li></ol>");
        const plain = '<p><strong>Use butter</strong> <a href="/recipes">here</a>.</p>';
        expect(renderIngredientAmounts(plain, root, [])).toBe(plain);
        expect(renderIngredientAmounts(html(), { ...root, total_ingredients: [] }, [])).toContain(
            "ingredient unavailable"
        );
    });

    test("separates amounts from adjacent words across inline formatting without spacing punctuation", () => {
        const token = `<span data-ingredient-amount="${encodeAmountReference(reference)}">{Butter:25%}</span>`;
        expect(renderIngredientAmounts(`<p>Melt ${token}butter.</p>`, root, [])).toBe(
            "<p>Melt <span>50 g </span>butter.</p>"
        );
        expect(
            renderIngredientAmounts(
                `<p>Add<strong>${token}</strong><em>cold butter</em>.</p>`,
                root,
                []
            )
        ).toBe("<p>Add<strong><span> 50 g </span></strong><em>cold butter</em>.</p>");
        expect(renderIngredientAmounts(`<p>Use (${token}), then stir.</p>`, root, [])).toBe(
            "<p>Use (<span>50 g</span>), then stir.</p>"
        );
    });

    test("validates saved references and escapes unavailable ingredient names in rendered HTML", () => {
        expect(decodeAmountReference(encodeAmountReference(reference))).toEqual(reference);
        for (const invalid of [
            null,
            "not-json",
            "%ZZ",
            encodeURIComponent('{"ingredientId":"butter"}'),
            encodeAmountReference({
                ...reference,
                path: [42]
            } as unknown as IngredientAmountReference)
        ]) {
            expect(decodeAmountReference(invalid)).toBeNull();
        }
        const unsafeReference = {
            ...reference,
            title: '<img src=x onerror="alert(1)">'
        };
        const result = renderIngredientAmounts(
            html(unsafeReference),
            { ...root, total_ingredients: [] },
            []
        );
        expect(result).toContain("&lt;img");
        expect(result).not.toContain("<img");
    });
});
