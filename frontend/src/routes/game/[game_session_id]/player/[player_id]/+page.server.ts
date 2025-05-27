import { redirect } from '@sveltejs/kit';
import { error } from '@sveltejs/kit';
import { createApiClient } from '$lib/api/api.js';
// import { createApiClient } from '$lib/api/api';
import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate, fail } from 'sveltekit-superforms';
import type { Actions } from './$types.js';
import { GameSessionPlayerUpdateSchema } from '$lib/schemas/schemas.js';

export const load = async ({ locals, url, parent, params, fetch }) => {
    const { authenticatedUser } = locals;
    const client = createApiClient(fetch); // Ensure fetch is passed if client uses it

    const parent_data = await parent();

    if (!authenticatedUser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

    const player = parent_data.game_session?.players?.find(p => p.id === params.player_id);

    if (!player) {
        error(404, 'Player not found');
    }

    // Initialize the form with the player's current name.
    // the drinks array is initialized with the drink information in the player object
    // if the player has no drinks, initialize with empty array
    const form = await superValidate({
        name: player.name,
        drinks: player.drink_links?.map((drink) => ({
            drink_id: drink.drink.id,
            amount: drink.amount
        })) || []
    }, zod(GameSessionPlayerUpdateSchema));

    return {
        form,
        player,
    };
};



export const actions = {
    default: async ({ fetch, request, cookies, params }) => {
        const auth_token = cookies.get("auth_token");
        const form = await superValidate(request, zod(GameSessionPlayerUpdateSchema));
        if (!auth_token) {
            redirect(302, "/auth/login");
        }
        if (!form.valid) {
            return fail(400, { form });
        }
        const client = createApiClient(fetch);
        // all drinks that are in in the form should be added with the amount 0
        const all_drinks = form.data.drinks.map((drink) => ({
            drink_id: drink.drink_id,
            amount: drink.amount
        }));




        const { data, error: apierror, response } = await client.PATCH("/game/{game_session_id}/player/{game_player_id}", {
            params: {
                path: {
                    game_session_id: params.game_session_id,
                    game_player_id: params.player_id,
                }
            },
            body: {
                name: form.data.name,
                drinks: all_drinks
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            console.error("API Error:", apierror);
            return fail(500, { form });
        }

        // return message(form, 'Player updated successfully')
        // redirect to last page
        redirect(303, "../")

    }

} satisfies Actions;