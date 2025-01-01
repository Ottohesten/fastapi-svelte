import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/heroes/");

    if (apierror) {
        error(404, apierror);
    }
    // console.log(data)




    return {
        heroes: data
    }
}
