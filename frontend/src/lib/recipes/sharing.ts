import type { RecipeIngredientTotalPublic } from "#lib/client/index.js";

export function parseServings(value: string | null, fallback: number): number {
    const servings = Number(value);
    return Number.isFinite(servings) && servings > 0 ? servings : fallback;
}

function formatAmount(value: number): string {
    return value.toFixed(2).replace(/\.?0+$/, "");
}

export function ingredientListText(
    title: string,
    servings: number,
    ingredients: Pick<RecipeIngredientTotalPublic, "title" | "amount" | "unit">[]
): string {
    return [
        title,
        `${formatAmount(servings)} ${servings === 1 ? "serving" : "servings"}`,
        "",
        ...ingredients.map((ingredient) =>
            `- ${formatAmount(ingredient.amount)} ${ingredient.unit} ${ingredient.title}`.replace(
                /\s+/g,
                " "
            )
        )
    ].join("\n");
}

export function scaledRecipeUrl(url: { href: string }, servings: number): URL {
    const result = new URL(url.href);
    result.searchParams.set("servings", String(servings));
    return result;
}
