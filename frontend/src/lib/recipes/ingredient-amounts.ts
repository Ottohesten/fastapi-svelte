import type { RecipeIngredientTotalPublic, RecipePublic } from "#lib/client/index.js";
import { defaultTreeAdapter, parseFragment, serialize } from "parse5";
import { attribute, isElement, type HtmlNode, type HtmlText } from "./html";

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
    return `${formatted} ${ingredient.unit}`.replace(/\s+/g, " ").trim();
}

export function renderIngredientAmounts(
    html: string,
    root: AmountRecipe,
    recipes: AmountRecipe[],
    servingsScale = 1
): string {
    if (!html.includes(AMOUNT_ATTRIBUTE)) return html;
    const fragment = parseFragment(html);
    const tokens: { text: string; node?: HtmlText; amount?: boolean }[] = [];
    const blocks = new Set(["p", "div", "li", "ol", "ul", "h1", "h2", "h3", "h4", "br", "pre"]);
    function walk(node: HtmlNode) {
        if (isElement(node)) {
            const reference = decodeAmountReference(attribute(node, AMOUNT_ATTRIBUTE));
            if (reference) {
                const amount = resolveIngredientAmount(reference, root, recipes, servingsScale);
                node.attrs =
                    amount === null
                        ? [{ name: "class", value: "text-amber-700 dark:text-amber-300" }]
                        : [];
                const text = amount ?? `${referenceLabel(reference)} (ingredient unavailable)`;
                const child = defaultTreeAdapter.createTextNode(text);
                node.childNodes = [];
                defaultTreeAdapter.appendChild(node, child);
                tokens.push({ text, node: child, amount: true });
                return;
            }
        }
        if (node.nodeName === "#text") {
            tokens.push({ text: (node as HtmlText).value });
        } else if ("childNodes" in node) {
            const block = isElement(node) && blocks.has(node.tagName);
            if (block) tokens.push({ text: "\n" });
            node.childNodes.forEach(walk);
            if (block) tokens.push({ text: "\n" });
        }
    }
    walk(fragment);
    for (const [index, token] of tokens.entries()) {
        if (!token.amount || !token.node) continue;
        const before = tokens[index - 1]?.text ?? "";
        const after = tokens[index + 1]?.text ?? "";
        // Chips have visual padding in the editor; keep words separated even when
        // the saved HTML omitted a literal space, including across inline marks.
        if (/[\p{L}\p{N}]$/u.test(before)) token.text = " " + token.text;
        if (/^[\p{L}\p{N}]/u.test(after)) token.text += " ";
        token.node.value = token.text;
    }
    return serialize(fragment);
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
