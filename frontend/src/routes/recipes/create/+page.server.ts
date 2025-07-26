import { createApiClient } from '$lib/api/api';
import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types.js';
import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate, fail } from 'sveltekit-superforms';
import { error } from '@sveltejs/kit';
import { RecipeSchema } from '$lib/schemas/schemas.js';


export const load = async ({ fetch, parent }) => {
    const client = createApiClient(fetch);

    // get the list of available ingredients
    const { data: ingredients, error: apierror, response } = await client.GET("/ingredients/");

    if (apierror) {
        return error(404, JSON.stringify(apierror.detail));
    }

    const form = await superValidate(zod(RecipeSchema));
    // const form = await superValidate({ ingredients: ingredients }, zod(RecipeSchema));
    return {
        ingredients: ingredients,
        form
    }
}


export const actions = {
    default: async ({ fetch, request, cookies }) => {
        const form = await superValidate(request, zod(RecipeSchema));

        if (!form.valid) {
            return fail(400, { form });
        }
        // return message(form, 'You have uploaded a valid file!');
        // return setError(form, 'image', 'Could not process file.');

        // post form data to the API
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        // Transform ingredients from frontend format to backend format
        const ingredientsForBackend = form.data.ingredients.map(ingredient => ({
            ingredient_id: ingredient.id,
            amount: ingredient.amount,
            unit: ingredient.unit
        }));

        const { data, error: apierror, response } = await client.POST("/recipes/", {
            body: {
                title: form.data.title,
                instructions: form.data.instructions ?? null,
                ingredients: ingredientsForBackend,
                servings: form.data.servings,
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }

        })

        if (apierror) {
            return fail(400, { form });
        }

        return redirect(302, "/recipes");
        // return message(form, "Form posted successfully!");
    }
} satisfies Actions;