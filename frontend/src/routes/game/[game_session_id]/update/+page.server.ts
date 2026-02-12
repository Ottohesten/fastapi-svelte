import { GameService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { zod4 } from "sveltekit-superforms/adapters";
import { z } from "zod";
import { message, superValidate, fail } from "sveltekit-superforms";
import { GameSessionTeamSchema, GameSessionPlayerSchema } from "$lib/schemas/schemas.js";

export const load = async ({ locals, url }) => {
    const { authenticatedUser } = locals;
    if (!authenticatedUser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }
    const teamForm = await superValidate(zod4(GameSessionTeamSchema), {
        id: "teamForm"
    });
    const playerForm = await superValidate(zod4(GameSessionPlayerSchema), {
        id: "playerForm"
    });

    return {
        teamForm,
        playerForm
    };
};

export const actions = {
    addTeam: async ({ fetch, params, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const teamForm = await superValidate(request, zod4(GameSessionTeamSchema));
        if (!teamForm.valid) {
            return fail(400, { teamForm });
        }

        const { error: apierror } = await GameService.CreateGameTeam({
            auth: () => auth_token,
            body: {
                name: teamForm.data.name
            },
            path: { game_session_id: params.game_session_id }
        });

        if (apierror) {
            return message(teamForm, `Error: ${apierror.detail}`);
        }
        // return message(teamForm, `Team ${teamForm.data.name} added successfully!`);
        // return message(teamForm, "Team added successfully!");
    },
    addPlayer: async ({ fetch, params, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const playerForm = await superValidate(request, zod4(GameSessionPlayerSchema));
        if (!playerForm.valid) {
            return fail(400, { playerForm });
        }

        const { error: apierror, response } = await GameService.CreateGamePlayer({
            auth: () => auth_token,
            body: {
                name: playerForm.data.name,
                team_id: playerForm.data.team_id || null
            },
            path: { game_session_id: params.game_session_id }
        });

        if (apierror) {
            return message(playerForm, `Error: ${apierror.detail}`);
            // error(404, JSON.stringify(apierror.detail));
        }
        // return message(playerForm, `Player ${playerForm.data.name} added successfully!`);
        // return message(playerForm, "Player added successfully!");
    },
    deleteTeam: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const game_session_id = formData.get("game_session_id") as string;
        const team_id = formData.get("team_id") as string;

        const { error: apierror, response } = await GameService.DeleteGameTeam({
            auth: () => auth_token,
            path: { game_session_id: game_session_id, game_team_id: team_id }
        });

        if (apierror) {
            error(404, JSON.stringify(apierror.detail));
        }
    },
    deletePlayer: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const game_session_id = formData.get("game_session_id") as string;
        const player_id = formData.get("player_id") as string;

        const { error: apierror, response } = await GameService.DeleteGamePlayer({
            auth: () => auth_token,
            path: { game_session_id: game_session_id, game_player_id: player_id }
        });

        if (apierror) {
            error(404, JSON.stringify(apierror.detail));
        }
    }
} satisfies Actions;
