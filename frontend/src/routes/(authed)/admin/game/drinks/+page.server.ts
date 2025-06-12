import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types.js';


export const load = async ({ fetch, params, locals }) => {
    const client = createApiClient(fetch);




    const { data: drinks, error: drinksError, response: drinksResponse } = await client.GET("/game/drinks",)

    if (drinksError) {
        error(drinksResponse.status, drinksError.detail?.toString());
    }
    return {
        drinks: drinks
    }
}


export const actions = {
    addDrink: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const name = formData.get('name') as string;

        if (!name || name.trim() === '') {
            return {
                error: 'Drink name is required'
            };
        }

        const { error: apierror, response } = await client.POST("/game/drinks", {
            body: {
                name: name.trim()
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            return {
                error: apierror.detail?.toString() || 'Failed to add drink'
            };
        }

        return {
            success: true
        };
    }
} satisfies Actions;