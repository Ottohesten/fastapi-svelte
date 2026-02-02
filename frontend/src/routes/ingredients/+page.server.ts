import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { message, superValidate, fail } from 'sveltekit-superforms';
import { zod4 as zod } from 'sveltekit-superforms/adapters';
import type { Actions } from './$types.js';
import { IngredientSchema } from '$lib/schemas/schemas.js';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/ingredients/");

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }
    // console.log(data)

    return {
        ingredients: data,
        ingredientCreateForm: await superValidate(zod(IngredientSchema))
    }
}

export const actions = {
    create: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        const form = await superValidate(request, zod(IngredientSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        const { data, error: apierror, response } = await client.POST("/ingredients/", {
            body: form.data,
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            return message(form, 'Failed to create ingredient: ' + JSON.stringify(apierror.detail), {
                status: 400
            });
        }

        return message(form, 'Ingredient created successfully!');
    },
    delete: async ({ fetch, params, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");


        const formData = await request.formData();
        const ingredient_id = formData.get("ingredient_id") as string;
        // console.log(ingredient_id);

        const { error: apierror, response } = await client.DELETE("/ingredients/{ingredient_id}", {
            params: {
                path: { ingredient_id: ingredient_id }
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        // return redirect(302, "/ingredients");
    }
} satisfies Actions;
