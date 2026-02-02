import { createApiClient } from '$lib/api/api';
import { error, fail, redirect } from '@sveltejs/kit';
import { message, superValidate } from 'sveltekit-superforms';
import { zod4 as zod } from 'sveltekit-superforms/adapters';
import type { Actions } from './$types.js';
import { DrinkSchema, DrinkUpdateSchema } from '$lib/schemas/schemas';

export const load = async ({ fetch }) => {
    const client = createApiClient(fetch);
    const { data: drinks, error: drinksError, response: drinksResponse } = await client.GET("/game/drinks");

    if (drinksError) {
        error(drinksResponse.status, drinksError.detail?.toString());
    }

    return {
        drinks: drinks,
        drinkCreateForm: await superValidate(zod(DrinkSchema), { id: 'drinkCreateForm' }),
        drinkUpdateForm: await superValidate(zod(DrinkUpdateSchema), { id: 'drinkUpdateForm' })
    }
}

export const actions = {
    addDrink: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) redirect(302, "/auth/login");

        const form = await superValidate(request, zod(DrinkSchema));
        if (!form.valid) return fail(400, { form });

        const { error: apierror } = await client.POST("/game/drinks", {
            body: form.data,
            headers: { Authorization: `Bearer ${auth_token}` }
        });

        if (apierror) {
            return message(form, apierror.detail?.toString() || 'Failed to add drink', { status: 400 });
        }

        return message(form, 'Drink added successfully');
    },

    updateDrink: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) redirect(302, "/auth/login");

        const form = await superValidate(request, zod(DrinkUpdateSchema));
        if (!form.valid) return fail(400, { form });

        const { id, name } = form.data;

        const { error: apierror } = await client.PATCH("/game/drinks/{drink_id}", {
            params: { path: { drink_id: id } },
            body: { name },
            headers: { Authorization: `Bearer ${auth_token}` }
        });

         if (apierror) {
            return message(form, apierror.detail?.toString() || 'Failed to update drink', { status: 400 });
        }

        return message(form, 'Drink updated successfully');
    },

    deleteDrink: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) redirect(302, "/auth/login");

        const formData = await request.formData();
        const drinkId = formData.get('drink_id') as string;

        const { error: apierror } = await client.DELETE("/game/drinks/{drink_id}", {
            params: { path: { drink_id: drinkId } },
            headers: { Authorization: `Bearer ${auth_token}` }
        });

        if (apierror) {
            return fail(400, { error: apierror.detail?.toString() || 'Failed to delete drink' });
        }

        return { success: true };
    }
} satisfies Actions;
