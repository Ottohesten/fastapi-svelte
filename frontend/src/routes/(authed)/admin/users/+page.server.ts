import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';

export const load = async ({ fetch, cookies }) => {
    const client = createApiClient(fetch);
    const auth_token = cookies.get("auth_token");
    const { data, error: apierror, response } = await client.GET("/users/", {
        headers: {
            Authorization: `Bearer ${auth_token}`
        }
    })

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }


    return {
        users: data
    }

}