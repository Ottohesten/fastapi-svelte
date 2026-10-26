import { describe, expect, test } from "bun:test";
import {
    encodeAmountReference,
    formAmountRecipe,
    renderIngredientAmounts
} from "./ingredient-amounts";
import {
    linkedInstructionBlock,
    linkSubRecipeInstructions,
    removeLinkedInstructions,
    resolveRecipeInstructions,
    type InstructionRecipe
} from "./sub-recipe-instructions";

function recipe(id: string, title: string, instructions: string, children: string[] = []) {
    return {
        ...formAmountRecipe(
            [],
            children.map((id) => ({ id, scale_factor: 1 })),
            []
        ),
        id,
        title,
        instructions
    };
}

describe("linked sub-recipe instructions", () => {
    test("refreshes old copied sections while preserving the parent's Assembly section", () => {
        const ragu = recipe("ragu", "Ragu", "<p>Latest ragu steps.</p>");
        const bechamel = recipe("bechamel", "Bechamel sauce", "<p>Latest bechamel steps.</p>");
        const lasagna = recipe(
            "lasagna",
            "Lasagne",
            "<h2>Bechamel sauce</h2><p>Old sauce.</p><h2>Ragu</h2><p>Old ragu.</p><h2>Assembly</h2><ol><li>Layer everything.</li></ol>",
            ["bechamel", "ragu"]
        );
        const first = resolveRecipeInstructions(lasagna, [bechamel, ragu]);
        expect(first).toContain("Latest ragu steps.");
        expect(first).toContain("Latest bechamel steps.");
        expect(first).not.toContain("Old");
        expect(first).toContain("<h2>Assembly</h2><ol><li>Layer everything.</li></ol>");
        ragu.instructions = "<p>Edited after linking.</p>";
        expect(resolveRecipeInstructions(lasagna, [bechamel, ragu])).toContain(
            "Edited after linking."
        );
        expect(lasagna.instructions).toContain("Old ragu.");
    });

    test("upgrades nested source headings into one stable link, preserving parent text", () => {
        const child = recipe(
            "ragu",
            "Ragu",
            "<h2>Preparation</h2><p>Dice onions.</p><h2>Sauce</h2><p>Cook.</p>"
        );
        const parent = recipe(
            "lasagna",
            "Lasagne",
            "<p>Start here.</p><h2>Ragu</h2><h2>Preparation</h2><p>Old prep.</p><h2>Sauce</h2><p>Old sauce.</p><h2>Assembly</h2><p>Layer.</p>",
            ["ragu"]
        );
        const canonical = linkSubRecipeInstructions(parent.instructions, parent.sub_recipe_links, [
            child
        ]);
        expect(canonical).toBe(
            `<p>Start here.</p>${linkedInstructionBlock(child)}<h2>Assembly</h2><p>Layer.</p>`
        );
        const renamed = { ...child, title: "Meat sauce" };
        expect(
            resolveRecipeInstructions({ ...parent, instructions: canonical }, [renamed])
        ).toContain("<h2>Meat sauce</h2>");
    });

    test("scales fresh ingredient references using the sub-recipe allocation", () => {
        const reference = encodeAmountReference({
            ingredientId: "butter",
            title: "Butter",
            unit: "g",
            portion: "100%",
            path: []
        });
        const child = {
            ...recipe(
                "ragu",
                "Ragu",
                `<p>Melt <span data-ingredient-amount="${reference}">{Butter:100%}</span>butter.</p>`
            ),
            total_ingredients: [{ ingredient_id: "butter", title: "Butter", amount: 30, unit: "g" }]
        };
        const parent = {
            ...recipe("lasagna", "Lasagne", linkedInstructionBlock(child), ["ragu"]),
            total_ingredients: [
                { ingredient_id: "butter", title: "Butter", amount: 100, unit: "g" }
            ]
        };
        expect(
            renderIngredientAmounts(resolveRecipeInstructions(parent, [child]), parent, [child], 2)
        ).toContain("<span>60 g </span>butter");
    });

    test("removes unlinked blocks and handles unavailable recipes and cycles", () => {
        const child = recipe("child", "Child", "<p>Child steps.</p>");
        const parent = recipe(
            "parent",
            "Parent",
            `${linkedInstructionBlock(child)}<h2>Assembly</h2><p>Keep this.</p>`,
            ["child"]
        );
        expect(removeLinkedInstructions(parent.instructions, "child")).toBe(
            "<h2>Assembly</h2><p>Keep this.</p>"
        );
        expect(resolveRecipeInstructions(parent, [])).toContain("instructions unavailable");
        expect(
            resolveRecipeInstructions({ ...parent, sub_recipe_links: [] }, [child])
        ).not.toContain("Child steps.");
        child.instructions = linkedInstructionBlock(parent);
        child.sub_recipe_links = (parent.sub_recipe_links ?? []).map((link) => ({
            ...link,
            sub_recipe: { ...link.sub_recipe, id: "parent" }
        }));
        expect(resolveRecipeInstructions(parent, [child, parent])).toContain(
            "instructions unavailable"
        );
    });

    test("does not infer links for unrelated or ambiguous headings", () => {
        const one = recipe("one", "Sauce", "<p>First.</p>");
        const two = recipe("two", "Sauce", "<p>Second.</p>");
        const parent = recipe("parent", "Parent", "<h2>Sauce</h2><p>My own instructions.</p>", [
            "one",
            "two"
        ]);
        expect(resolveRecipeInstructions(parent, [one, two])).toBe(parent.instructions);
        const plain: InstructionRecipe = { ...parent, sub_recipe_links: [] };
        expect(resolveRecipeInstructions(plain, [one])).toBe(parent.instructions);
    });
});
