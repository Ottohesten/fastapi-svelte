import { RecipesService } from "#lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";
import type { RecipePublic } from "#lib/client/index.js";

export const load = async ({ fetch, params, locals, cookies }) => {
    const auth_token = cookies.get("auth_token");
    const headers = auth_token ? { Authorization: `Bearer ${auth_token}` } : undefined;

    const {
        data,
        error: apierror,
        response
    } = await RecipesService.GetRecipe({
        fetch,
        path: { recipe_id: params.slug },
        headers
    });

    if (apierror) {
        error(response?.status ?? 502, apierror.detail?.toString());
    }

    // Load linked instructions afresh on each recipe visit. The recipes-list
    // layout may be reused when navigating back from a sub-recipe editor.
    const visited = new Set<string>([data.id]);
    const instructionRecipes: RecipePublic[] = [];
    async function collectInstructions(recipe: RecipePublic): Promise<void> {
        await Promise.all(
            (recipe.sub_recipe_links ?? []).map(async (link) => {
                const id = link.sub_recipe.id;
                if (visited.has(id)) return;
                visited.add(id);
                const result = await RecipesService.GetRecipe({
                    fetch,
                    path: { recipe_id: id },
                    headers
                });
                if (result.error) {
                    const status = result.response?.status ?? 502;
                    if (status === 403 || status === 404) return;
                    error(status, "Could not load linked recipe instructions");
                }
                instructionRecipes.push(result.data);
                await collectInstructions(result.data);
            })
        );
    }
    await collectInstructions(data);

    const scopes = locals.authenticatedUser?.scopes ?? [];
    const is_owner = locals.authenticatedUser
        ? data.owner.id === locals.authenticatedUser.id
        : false;
    const can_edit =
        !!locals.authenticatedUser &&
        (locals.authenticatedUser.is_superuser || is_owner || scopes.includes("recipes:update"));
    const can_log = !!locals.authenticatedUser && scopes.includes("nutrition:use");

    return {
        recipe: data,
        instructionRecipes,
        is_owner,
        can_edit,
        can_log
    };
};
