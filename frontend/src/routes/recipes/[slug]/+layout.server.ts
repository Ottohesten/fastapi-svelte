import { RecipesService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";

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
        error(response.status, apierror.detail?.toString());
    }

    const scopes = locals.authenticatedUser?.scopes ?? [];
    const is_owner = locals.authenticatedUser
        ? data.owner.id === locals.authenticatedUser.id
        : false;
    const can_edit =
        !!locals.authenticatedUser &&
        (locals.authenticatedUser.is_superuser || is_owner || scopes.includes("recipes:update"));

    return {
        recipe: data,
        is_owner,
        can_edit
    };
};
