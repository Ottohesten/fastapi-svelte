import { redirect } from '@sveltejs/kit';
import { error } from '@sveltejs/kit';
import { createApiClient } from '$lib/api/api.js';
// import { createApiClient } from '$lib/api/api';
import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate, fail } from 'sveltekit-superforms';
import type { Actions } from './$types.js';
import { RecipeSchema } from '$lib/schemas/schemas.js';


export async function load({ fetch, params, locals, request, parent, url }) {
    const { authenticatedUser } = locals;
    const recipe_id = params.slug
    const parent_data = await parent()

    // if there is no user redirect to login page
    if (!authenticatedUser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

    // if user is not superuser, or is not the owner of the recipe, return 403 forbidden
    if (!authenticatedUser?.is_superuser && !parent_data.is_owner) {
        error(403, "Forbidden");
    }

    // Get the list of available ingredients
    const client = createApiClient(fetch);
    const { data: allIngredients, error: apierror, response } = await client.GET("/ingredients/");

    if (apierror) {
        return error(404, JSON.stringify(apierror.detail));
    }

    // Transform the backend ingredient_links to frontend ingredients format
    const frontendIngredients = parent_data.recipe.ingredient_links.map(link => ({
        id: link.ingredient.id,
        title: link.ingredient.title, // Include title for display
        amount: link.amount,
        unit: link.unit as "g" | "kg" | "ml" | "L" | "pcs"
    }));

    // Filter out ingredients that are already in the recipe
    const usedIngredientIds = new Set(frontendIngredients.map(ing => ing.id));
    const availableIngredients = allIngredients.filter(ing => !usedIngredientIds.has(ing.id));

    const form = await superValidate({
        ingredients: frontendIngredients,
        title: parent_data.recipe.title,
        instructions: parent_data.recipe.instructions ?? undefined,
        servings: parent_data.recipe.servings ?? 1
    }, zod(RecipeSchema));

    return {
        ingredients: availableIngredients,
        form
    }
}


export const actions = {
    default: async ({ fetch, request, cookies, params }) => {
        const form = await superValidate(request, zod(RecipeSchema));
        console.log(form)
        if (!form.valid) {
            return fail(400, { form });
        }

        // Transform ingredients from frontend format to backend format
        const ingredientsForBackend = form.data.ingredients.map(ingredient => ({
            ingredient_id: ingredient.id,
            amount: ingredient.amount,
            unit: ingredient.unit
        }));

        // TODO: Implement PATCH endpoint in backend
        console.log("Update data would be sent:", {
            title: form.data.title,
            instructions: form.data.instructions ?? null,
            ingredients: ingredientsForBackend,
            servings: form.data.servings,
        });

        // For now, just redirect back to show the form works
        return redirect(302, "/recipes");

        // post form data to the API (when backend PATCH is implemented)
        // const client = createApiClient(fetch);
        // const auth_token = cookies.get("auth_token");

        // const { data, error: apierror, response } = await client.PATCH("/recipes/{recipe_id}", {
        //     params: {
        //         path: { recipe_id: params.slug }
        //     },
        //     body: {
        //         title: form.data.title,
        //         instructions: form.data.instructions ?? null,
        //         ingredients: ingredientsForBackend,
        //         servings: form.data.servings,
        //     },
        //     headers: {
        //         Authorization: `Bearer ${auth_token}`
        //     }
        // })

        // if (apierror) {
        //     console.log("apierror in recipes/[slug]/update/[page.server.ts file", apierror);
        //     error(404, JSON.stringify(apierror.detail));
        // }

        // return redirect(302, "/recipes");
    }
} satisfies Actions;
