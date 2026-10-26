import type { RecipeIngredientTotalPublic, RecipePublic } from "$lib/client";

export type AmountIngredient = Pick<
    RecipeIngredientTotalPublic,
    "ingredient_id" | "title" | "amount" | "unit"
>;
export type AmountRecipe = Pick<RecipePublic, "id" | "sub_recipe_links"> & {
    total_ingredients: AmountIngredient[];
};
export type IngredientAmountReference = {
    ingredientId: string;
    unit: string;
    portion: string;
    title: string;
    path: string[];
};

export const AMOUNT_ATTRIBUTE = "data-ingredient-amount";
// Only our serialized, text-only inline nodes are replaced; surrounding HTML is untouched.
const AMOUNT_NODE = /<span\b[^>]*\bdata-ingredient-amount="([^"]*)"[^>]*>[^<]*<\/span>/g;

export function parseIngredientPortion(value: string): number | null {
    const percent = value.trim().match(/^(\d+(?:\.\d+)?)\s*%$/);
    const fraction = value.trim().match(/^(\d+)\s*\/\s*(\d+)$/);
    const ratio = percent
        ? Number(percent[1]) / 100
        : fraction
          ? Number(fraction[1]) / Number(fraction[2])
          : NaN;
    return Number.isFinite(ratio) && ratio > 0 && ratio <= 1 ? ratio : null;
}

export function encodeAmountReference(reference: IngredientAmountReference): string {
    return encodeURIComponent(JSON.stringify(reference));
}

export function decodeAmountReference(value: unknown): IngredientAmountReference | null {
    if (typeof value !== "string") return null;
    try {
        const reference = JSON.parse(decodeURIComponent(value));
        if (
            !reference ||
            typeof reference.ingredientId !== "string" ||
            !reference.ingredientId ||
            typeof reference.unit !== "string" ||
            typeof reference.title !== "string" ||
            typeof reference.portion !== "string" ||
            parseIngredientPortion(reference.portion) === null ||
            !Array.isArray(reference.path) ||
            !reference.path.every((id: unknown) => typeof id === "string" && id.length > 0)
        ) {
            return null;
        }
        return reference;
    } catch {
        return null;
    }
}

export function referenceLabel(reference: IngredientAmountReference): string {
    return `{${reference.title}:${reference.portion}}`;
}

export function ingredientReferenceFromToken(
    token: string,
    ingredients: AmountIngredient[]
): IngredientAmountReference | null {
    const match = token.match(/^\{([^{}]+):([^{}:]+)\}$/);
    if (!match || parseIngredientPortion(match[2]) === null) return null;
    const name = match[1].trim().match(/^(.*?)(?:\s*\[([^\]]+)\])?$/);
    if (!name) return null;
    const matches = ingredients.filter(
        (ingredient) =>
            ingredient.title.trim().toLowerCase() === name[1].trim().toLowerCase() &&
            (!name[2] || ingredient.unit === name[2])
    );
    // Ambiguous names or units must be selected explicitly in the picker.
    if (matches.length !== 1) return null;
    return {
        ingredientId: matches[0].ingredient_id,
        title: matches[0].title,
        unit: matches[0].unit,
        portion: match[2].trim(),
        path: []
    };
}

export function ingredientAmountScope(
    path: string[],
    root: AmountRecipe,
    recipes: AmountRecipe[]
): { recipe: AmountRecipe; scale: number } | null {
    let recipe = root;
    let scale = 1;
    for (const id of path) {
        const link = recipe.sub_recipe_links?.find((link) => link.sub_recipe.id === id);
        const child = recipes.find((candidate) => candidate.id === id);
        if (!link || !child) return null;
        scale *= link.scale_factor;
        recipe = child;
    }
    return { recipe, scale };
}

export function resolveIngredientAmount(
    reference: IngredientAmountReference,
    root: AmountRecipe,
    recipes: AmountRecipe[],
    servingsScale = 1
): string | null {
    const scope = ingredientAmountScope(reference.path, root, recipes);
    const ingredient = scope?.recipe.total_ingredients.find(
        (ingredient) =>
            ingredient.ingredient_id === reference.ingredientId &&
            ingredient.unit === reference.unit
    );
    const ratio = parseIngredientPortion(reference.portion);
    if (!scope || !ingredient || ratio === null) return null;
    const amount = ingredient.amount * scope.scale * servingsScale * ratio;
    if (!Number.isFinite(amount)) return null;
    const formatted = amount.toFixed(2).replace(/\.?0+$/, "");
    return `${formatted} ${ingredient.unit} ${ingredient.title}`.replace(/\s+/g, " ").trim();
}

function escapeHtml(value: string): string {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

export function renderIngredientAmounts(
    html: string,
    root: AmountRecipe,
    recipes: AmountRecipe[],
    servingsScale = 1
): string {
    return html.replace(AMOUNT_NODE, (original, encoded: string) => {
        const reference = decodeAmountReference(encoded);
        if (!reference) return original;
        const amount = resolveIngredientAmount(reference, root, recipes, servingsScale);
        return amount === null
            ? `<span class="text-amber-700 dark:text-amber-300">${escapeHtml(referenceLabel(reference))} (ingredient unavailable)</span>`
            : `<span>${escapeHtml(amount)}</span>`;
    });
}

export function scopeImportedIngredientAmounts(html: string, recipeId: string): string {
    return html.replace(AMOUNT_NODE, (original, encoded: string) => {
        const reference = decodeAmountReference(encoded);
        if (!reference) return original;
        return original.replace(
            `data-ingredient-amount="${encoded}"`,
            `data-ingredient-amount="${encodeAmountReference({ ...reference, path: [recipeId, ...reference.path] })}"`
        );
    });
}

export function formAmountRecipe(
    ingredients: { id: string; title?: string; amount: number; unit: string }[],
    subRecipes: { id: string; scale_factor: number }[],
    recipes: AmountRecipe[]
): AmountRecipe {
    const totals = new Map<string, AmountIngredient>();
    function add(ingredient: AmountIngredient) {
        const unit =
            ingredient.unit === "kg" ? "g" : ingredient.unit === "L" ? "ml" : ingredient.unit;
        const amount =
            ingredient.amount * (ingredient.unit === "kg" || ingredient.unit === "L" ? 1000 : 1);
        const key = JSON.stringify([ingredient.ingredient_id, unit]);
        const previous = totals.get(key);
        totals.set(key, { ...ingredient, unit, amount: amount + (previous?.amount ?? 0) });
    }
    for (const ingredient of ingredients) {
        add({
            ...ingredient,
            ingredient_id: ingredient.id,
            title: ingredient.title ?? ingredient.id
        });
    }
    for (const link of subRecipes) {
        const recipe = recipes.find((recipe) => recipe.id === link.id);
        for (const ingredient of recipe?.total_ingredients ?? []) {
            add({ ...ingredient, amount: ingredient.amount * link.scale_factor });
        }
    }
    return {
        id: "",
        total_ingredients: [...totals.values()],
        sub_recipe_links: subRecipes.map((link) => ({
            sub_recipe: { id: link.id, title: "", servings: 1 },
            scale_factor: link.scale_factor,
            scaled_servings: link.scale_factor
        }))
    };
}
