import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types.js';
import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate, fail } from 'sveltekit-superforms';
import { GameSessionTeamSchema } from '$lib/schemas/schemas.js';

export const load = async ({ }) => {
    const form = await superValidate(zod(GameSessionTeamSchema));

    return {
        form
    }
}



export const actions = {
    addTeam: async ({ fetch, params, cookies, request }) => {
        const auth_token = cookies.get("auth_token");
        const form = await superValidate(request, zod(GameSessionTeamSchema));
        if (!auth_token) {
            redirect(302, "/auth/login");
        }
        if (!form.valid) {
            return fail(400, { form });
        }

        const client = createApiClient(fetch);

        const { error: apierror, response } = await client.POST("/game/{game_session_id}/team", {
            body: {
                name: form.data.title,
            },
            params: {
                path: { game_session_id: params.slug }
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
    }

} satisfies Actions;