import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';


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