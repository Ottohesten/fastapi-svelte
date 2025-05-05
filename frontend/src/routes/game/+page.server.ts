import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/game/");

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }

    return {
        game_sessions: data
    }
}