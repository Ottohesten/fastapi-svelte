import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';


export const load = async ({ fetch, params }) => {
    const client = createApiClient(fetch);
    // const { data, error } = await client.GET("/heroes/{hero_id}");
    const { data, error: apierror, response } = await client.GET("/heroes/{hero_id}", {
        params: {
            path: { hero_id: parseInt(params.slug) }
        }
    });
    // console.log(response.status)
    // console.log(error)
    if (apierror) {
        error(response.status, apierror.detail?.toString());
    }

    return {
        hero: data
    }
}
