import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types.js';
import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate, fail } from 'sveltekit-superforms';
import { GameSessionTeamSchema, GameSessionPlayerSchema } from '$lib/schemas/schemas.js';

export const load = async ({ fetch, params, cookies }) => {
    const teamForm = await superValidate(zod(GameSessionTeamSchema), {
        id: "teamForm",
    });
    const playerForm = await superValidate(zod(GameSessionPlayerSchema), {
        id: "playerForm",
    });

    // Fetch initial game session snapshot (public)
    let game_session = null;
    try {
        const client = createApiClient(fetch);
        const { data, error: apierror } = await client.GET('/game/{game_session_id}', {
            params: { path: { game_session_id: params.game_session_id } }
        });
        if (!apierror) {
            game_session = data;
        }
    } catch (e) {
        // ignore; page can still render forms
    }

    return {
        teamForm,
        playerForm,
        game_session
    }
}



export const actions = {
    addTeam: async ({ fetch, params, cookies, request }) => {
        const auth_token = cookies.get("auth_token");
        const teamForm = await superValidate(request, zod(GameSessionTeamSchema));
        if (!auth_token) {
            redirect(302, "/auth/login");
        }
        if (!teamForm.valid) {
            return fail(400, { teamForm });
        }

        const client = createApiClient(fetch);

        const { error: apierror, response } = await client.POST("/game/{game_session_id}/team", {
            body: {
                name: teamForm.data.name,
            },
            params: {
                path: { game_session_id: params.game_session_id }
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
        // return message(teamForm, `Team ${teamForm.data.name} added successfully!`);
        // return message(teamForm, "Team added successfully!");
    },
    addPlayer: async ({ fetch, params, cookies, request }) => {
        const auth_token = cookies.get("auth_token");
        const playerForm = await superValidate(request, zod(GameSessionPlayerSchema));
        if (!auth_token) {
            redirect(302, "/auth/login");
        }
        if (!playerForm.valid) {
            return fail(400, { playerForm });
        }

        const client = createApiClient(fetch);

        const { error: apierror, response } = await client.POST("/game/{game_session_id}/player", {
            body: {
                name: playerForm.data.name,
                team_id: playerForm.data.team_id || null,
            },
            params: {
                path: { game_session_id: params.game_session_id }
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
        // return message(playerForm, `Player ${playerForm.data.name} added successfully!`);
        // return message(playerForm, "Player added successfully!");
    },
    deleteTeam: async ({ fetch, params, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const game_session_id = formData.get("game_session_id") as string;
        const team_id = formData.get("team_id") as string;

        const { error: apierror, response } = await client.DELETE("/game/{game_session_id}/team/{game_team_id}", {
            params: {
                path: { game_session_id: game_session_id, game_team_id: team_id }
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

    },
    deletePlayer: async ({ fetch, params, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const game_session_id = formData.get("game_session_id") as string;
        const player_id = formData.get("player_id") as string;

        const { error: apierror, response } = await client.DELETE("/game/{game_session_id}/player/{game_player_id}", {
            params: {
                path: { game_session_id: game_session_id, game_player_id: player_id }
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

    },
    addDrinkToPlayer: async ({ fetch, params, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const player_id = formData.get("player_id") as string;
        const drink_id = formData.get("drink_id") as string;
        const amount = formData.get("amount") as string;
        const { data, error: apierror, response } = await client.PATCH("/game/{game_session_id}/player/{game_player_id}/drink", {
            params: {
                path: {
                    game_session_id: params.game_session_id,
                    game_player_id: player_id,
                }
            },
            body: {
                drink_id: drink_id,
                amount: amount ? parseInt(amount as string) : 0
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            // log with file name
            // console.log("apierror in game/+page.server.ts", apierror);
            error(404, JSON.stringify(apierror.detail));
        }

        // return message(form, 'Player updated successfully')
        // redirect to last page
        redirect(303, "/game/" + params.game_session_id);

    }


} satisfies Actions;