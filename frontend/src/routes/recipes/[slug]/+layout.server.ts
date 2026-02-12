import { RecipesService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";

export const load = async ({ fetch, params, locals }) => {
    const {
        data,
        error: apierror,
        response
    } = await RecipesService.ReadRecipe({
        fetch,
        path: { recipe_id: params.slug }
    });

    if (apierror) {
        error(response.status, apierror.detail?.toString());
    }

    return {
        recipe: data,
        is_owner: locals.authenticatedUser ? data.owner.id === locals.authenticatedUser.id : false
    };
};
