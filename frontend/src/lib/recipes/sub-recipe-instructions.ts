import type { RecipePublic } from "$lib/client";
import { parseFragment, serialize, serializeOuter } from "parse5";
import { scopeImportedIngredientAmounts } from "./ingredient-amounts";
import {
    attribute,
    escapeHtml,
    isElement,
    textContent,
    type HtmlChild,
    type HtmlParent
} from "./html";

export const SUB_RECIPE_ATTRIBUTE = "data-sub-recipe-instructions";
export type InstructionRecipe = Pick<
    RecipePublic,
    "id" | "title" | "instructions" | "sub_recipe_links"
>;

export function linkedInstructionBlock(recipe: Pick<InstructionRecipe, "id" | "title">): string {
    return `<div ${SUB_RECIPE_ATTRIBUTE}="${escapeHtml(recipe.id)}" data-sub-recipe-title="${escapeHtml(recipe.title)}">${escapeHtml(recipe.title)}</div>`;
}

/** Replace old copied H2 sections with stable links, keeping the parent's own sections. */
export function linkSubRecipeInstructions(
    html: string,
    links: InstructionRecipe["sub_recipe_links"],
    recipes: InstructionRecipe[]
): string {
    if (!links?.length || !/<h2\b/i.test(html)) return html;
    const children = links
        .map((link) => recipes.find((recipe) => recipe.id === link.sub_recipe.id))
        .filter((recipe): recipe is InstructionRecipe => !!recipe);
    const fragment = parseFragment(html);
    const nodes = fragment.childNodes;
    let changed = false;
    const result: string[] = [];
    for (let index = 0; index < nodes.length; index++) {
        const node = nodes[index];
        const matches =
            isElement(node) && node.tagName === "h2"
                ? children.filter(
                      (recipe) =>
                          recipe.title.trim().toLowerCase() ===
                          textContent(node).trim().toLowerCase()
                  )
                : [];
        if (matches.length !== 1) {
            result.push(serializeOuter(node));
            continue;
        }
        const child = matches[0];
        const headings = new Set(
            parseFragment(child.instructions)
                .childNodes.filter((node) => isElement(node) && node.tagName === "h2")
                .map((node) => textContent(node).trim().toLowerCase())
        );
        result.push(linkedInstructionBlock(child));
        changed = true;
        while (index + 1 < nodes.length) {
            const next = nodes[index + 1];
            if (attribute(next, SUB_RECIPE_ATTRIBUTE)) break;
            if (isElement(next) && /^h[12]$/.test(next.tagName)) {
                const title = textContent(next).trim().toLowerCase();
                if (
                    next.tagName === "h1" ||
                    children.some((recipe) => recipe.title.trim().toLowerCase() === title) ||
                    !headings.has(title)
                )
                    break;
            }
            index++;
        }
    }
    return changed ? result.join("") : html;
}

export function removeLinkedInstructions(html: string, recipeId: string): string {
    const fragment = parseFragment(html);
    function remove(parent: HtmlParent) {
        parent.childNodes = parent.childNodes.filter(
            (node) => attribute(node, SUB_RECIPE_ATTRIBUTE) !== recipeId
        );
        parent.childNodes.forEach((node) => {
            if ("childNodes" in node) remove(node);
        });
    }
    remove(fragment);
    return serialize(fragment);
}

export function resolveRecipeInstructions(
    recipe: InstructionRecipe,
    recipes: InstructionRecipe[]
): string {
    function expand(current: InstructionRecipe, ancestors: Set<string>): string {
        const html = linkSubRecipeInstructions(
            current.instructions ?? "",
            current.sub_recipe_links,
            recipes
        );
        if (!html.includes(SUB_RECIPE_ATTRIBUTE)) return html;
        const fragment = parseFragment(html);
        function replace(parent: HtmlParent) {
            const children: HtmlChild[] = [];
            for (const node of parent.childNodes) {
                const id = attribute(node, SUB_RECIPE_ATTRIBUTE);
                if (!id) {
                    if ("childNodes" in node) replace(node);
                    children.push(node);
                    continue;
                }
                // Only expand actual links using recipes visible to this user.
                if (!current.sub_recipe_links?.some((link) => link.sub_recipe.id === id)) continue;
                const child = recipes.find((candidate) => candidate.id === id);
                const unavailable = !child || ancestors.has(id);
                const title =
                    child?.title ?? attribute(node, "data-sub-recipe-title") ?? "Sub-recipe";
                const body = unavailable
                    ? "<p>Sub-recipe instructions unavailable.</p>"
                    : scopeImportedIngredientAmounts(
                          expand(child, new Set([...ancestors, id])),
                          id
                      );
                const replacement = parseFragment(`<h2>${escapeHtml(title)}</h2>${body}`);
                for (const replacementNode of replacement.childNodes) {
                    replacementNode.parentNode = parent;
                    children.push(replacementNode);
                }
            }
            parent.childNodes = children;
        }
        replace(fragment);
        return serialize(fragment);
    }
    return expand(recipe, new Set([recipe.id]));
}
