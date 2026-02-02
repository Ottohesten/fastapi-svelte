import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types.js';
import { zod4 as zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate, fail } from 'sveltekit-superforms';
import { GameSessionTeamSchema } from '$lib/schemas/schemas.js';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/game/");

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }

    const form = await superValidate(zod(GameSessionTeamSchema));

    return {
        game_sessions: data,
        form
    }
}


export const actions = {
    deleteGame: async ({ fetch, params, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const game_session_id = formData.get("game_session_id") as string;

        const { error: apierror, response } = await client.DELETE("/game/{game_session_id}", {
            params: {
                path: { game_session_id: game_session_id }
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            // log with file name
            // console.log("apierror in game/+page.server.ts", apierror);
            error(404, JSON.stringify(apierror.detail));
        }

        // return redirect(302, "/recipes");
    },

} satisfies Actions;
