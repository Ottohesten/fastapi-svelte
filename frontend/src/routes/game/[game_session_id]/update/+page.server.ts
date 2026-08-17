import { GameService } from "$lib/client/sdk.gen.js";
import { GameSessionPlayerSchema, GameSessionTeamSchema } from "$lib/schemas/schemas.js";
import { error, redirect } from "@sveltejs/kit";
import { fail, message, superValidate } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { z } from "zod";
import type { Actions, PageServerLoad } from "./$types.js";

const entityIdSchema = z.string().uuid();

function requireGameManager(locals: App.Locals, url: URL) {
    const { authenticatedUser } = locals;

    if (!authenticatedUser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

    if (!authenticatedUser.scopes?.includes("games:update")) {
        error(403, "You do not have permission to manage game sessions.");
    }
}

function getApiErrorMessage(apiError: unknown, fallback: string) {
    if (!apiError || typeof apiError !== "object" || !("detail" in apiError)) {
        return fallback;
    }

    const detail = apiError.detail;
    return typeof detail === "string" ? detail : fallback;
}

export const load: PageServerLoad = async ({ locals, url }) => {
    requireGameManager(locals, url);

    const [teamForm, playerForm] = await Promise.all([
        superValidate(zod(GameSessionTeamSchema), { id: "teamForm" }),
        superValidate(zod(GameSessionPlayerSchema), { id: "playerForm" })
    ]);

    return {
        teamForm,
        playerForm
    };
};

export const actions = {
    addTeam: async ({ params, cookies, request, url, locals }) => {
        requireGameManager(locals, url);

        const authToken = cookies.get("auth_token");
        if (!authToken) {
            redirect(303, `/auth/login?redirectTo=${url.pathname}`);
        }

        const teamForm = await superValidate(request, zod(GameSessionTeamSchema), {
            id: "teamForm"
        });
        if (!teamForm.valid) {
            return fail(400, { teamForm });
        }

        const { error: apiError } = await GameService.CreateGameTeam({
            auth: authToken,
            body: { name: teamForm.data.name },
            path: { game_session_id: params.game_session_id }
        });

        if (apiError) {
            return message(teamForm, getApiErrorMessage(apiError, "The team could not be added."), {
                status: 400
            });
        }

        return message(teamForm, `${teamForm.data.name} was added.`);
    },

    addPlayer: async ({ params, cookies, request, url, locals }) => {
        requireGameManager(locals, url);

        const authToken = cookies.get("auth_token");
        if (!authToken) {
            redirect(303, `/auth/login?redirectTo=${url.pathname}`);
        }

        const playerForm = await superValidate(request, zod(GameSessionPlayerSchema), {
            id: "playerForm"
        });
        if (!playerForm.valid) {
            return fail(400, { playerForm });
        }

        const { error: apiError } = await GameService.CreateGamePlayer({
            auth: authToken,
            body: {
                name: playerForm.data.name,
                team_id: playerForm.data.team_id || null
            },
            path: { game_session_id: params.game_session_id }
        });

        if (apiError) {
            return message(
                playerForm,
                getApiErrorMessage(apiError, "The player could not be added."),
                { status: 400 }
            );
        }

        return message(playerForm, `${playerForm.data.name} was added.`);
    },

    deleteTeam: async ({ params, cookies, request, url, locals }) => {
        requireGameManager(locals, url);

        const authToken = cookies.get("auth_token");
        if (!authToken) {
            redirect(303, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const parsedTeamId = entityIdSchema.safeParse(formData.get("team_id"));
        if (!parsedTeamId.success) {
            return fail(400, {
                operation: "deleteTeam" as const,
                error: "A valid team is required."
            });
        }

        const { error: apiError } = await GameService.DeleteGameTeam({
            auth: authToken,
            path: {
                game_session_id: params.game_session_id,
                game_team_id: parsedTeamId.data
            }
        });

        if (apiError) {
            return fail(400, {
                operation: "deleteTeam" as const,
                error: getApiErrorMessage(apiError, "The team could not be deleted.")
            });
        }

        return { success: true, operation: "deleteTeam" as const };
    },

    deletePlayer: async ({ params, cookies, request, url, locals }) => {
        requireGameManager(locals, url);

        const authToken = cookies.get("auth_token");
        if (!authToken) {
            redirect(303, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const parsedPlayerId = entityIdSchema.safeParse(formData.get("player_id"));
        if (!parsedPlayerId.success) {
            return fail(400, {
                operation: "deletePlayer" as const,
                error: "A valid player is required."
            });
        }

        const { error: apiError } = await GameService.DeleteGamePlayer({
            auth: authToken,
            path: {
                game_session_id: params.game_session_id,
                game_player_id: parsedPlayerId.data
            }
        });

        if (apiError) {
            return fail(400, {
                operation: "deletePlayer" as const,
                error: getApiErrorMessage(apiError, "The player could not be deleted.")
            });
        }

        return { success: true, operation: "deletePlayer" as const };
    }
} satisfies Actions;
