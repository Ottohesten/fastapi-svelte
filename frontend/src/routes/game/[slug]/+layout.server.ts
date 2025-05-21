import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';


export const load = async ({ fetch, params, locals }) => {
    const client = createApiClient(fetch);

    const { data, error: apierror, response } = await client.GET("/game/{game_session_id}", {
        params: {
            path: { game_session_id: params.slug }
        }
    });

    if (apierror) {
        error(response.status, apierror.detail?.toString());
    }

    return {
        game_session: data,
        is_owner: locals.authenticatedUser ? data.owner.id === locals.authenticatedUser.id : false
    }
}