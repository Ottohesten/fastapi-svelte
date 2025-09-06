import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/recipes/");


    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }
    // console.log(data)

    const { data: ingredients, error: apierror_2, response: response_2 } = await client.GET("/ingredients/");

    if (apierror_2) {
        return error(404, JSON.stringify(apierror_2.detail));
    }



    return {
        recipes: data,
        ingredients: ingredients,
        authenticatedUser: locals.authenticatedUser,
        scopes: locals.authenticatedUser?.scopes ?? []
    }
}



