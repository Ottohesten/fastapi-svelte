import { createApiClient } from '$lib/api/api';
import { error, fail } from '@sveltejs/kit';
import { message, superValidate } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import type { Actions } from './$types.js';
import { IngredientSchema } from '$lib/schemas/schemas.js';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/ingredients/");

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }

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
    update: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        const formData = await request.formData();
        const id = formData.get('id') as string;
        const title = formData.get('title') as string;
        const calories = parseInt(formData.get('calories') as string);
        const weight_per_piece = parseInt(formData.get('weight_per_piece') as string);

        if (!id || !title || isNaN(calories) || isNaN(weight_per_piece)) {
            return fail(400, { error: 'Invalid data provided' });
        }

        const { error: apierror } = await client.PATCH("/ingredients/{ingredient_id}", {
            params: {
                path: { ingredient_id: id }
            },
            body: {
                title,
                calories,
                weight_per_piece
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            return fail(400, { error: 'Failed to update ingredient' });
        }

        return { success: true };
    },
    delete: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        const formData = await request.formData();
        const id = formData.get('id') as string;

        if (!id) {
            return fail(400, { error: 'Ingredient ID is required' });
        }

        const { error: apierror } = await client.DELETE("/ingredients/{ingredient_id}", {
            params: {
                path: { ingredient_id: id }
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            return fail(400, { error: 'Failed to delete ingredient' });
        }

        return { success: true };
    }
} satisfies Actions;
