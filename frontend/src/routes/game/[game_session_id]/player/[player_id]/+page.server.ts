import { GameService } from "$lib/client/sdk.gen.js";
import { GameSessionPlayerUpdateSchema } from "$lib/schemas/schemas.js";
import { error, redirect } from "@sveltejs/kit";
import { fail, message, superValidate } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import type { Actions, PageServerLoad } from "./$types.js";

export const load: PageServerLoad = async ({ parent, params }) => {
    const parent_data = await parent();

    const player = parent_data.game_session?.players?.find((p) => p.id === params.player_id);

    if (!player) {
        error(404, "Player not found");
    }

    const form = await superValidate(
        {
            name: player.name,
            team_id: player.team_id ?? null,
            drinks:
                player.drink_links?.map((drink) => ({
                    drink_id: drink.drink.id,
                    amount: drink.amount
                })) || []
        },
        zod(GameSessionPlayerUpdateSchema)
    );

    return {
        form,
        player
    };
};

export const actions = {
    default: async ({ request, cookies, params, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const form = await superValidate(request, zod(GameSessionPlayerUpdateSchema));
        if (!form.valid) {
            return fail(400, { form });
        }

        const drinks = form.data.drinks.map((drink) => ({
            drink_id: drink.drink_id,
            amount: drink.amount
        }));

        const { error: apierror } = await GameService.UpdateGamePlayer({
            auth: auth_token,
            body: {
                name: form.data.name,
                team_id: form.data.team_id || null,
                drinks
            },
            path: {
                game_session_id: params.game_session_id,
                game_player_id: params.player_id
            }
        });

        if (apierror) {
            const detail =
                typeof apierror.detail === "string"
                    ? apierror.detail
                    : "The player could not be updated.";
            return message(form, detail, { status: 400 });
        }

        redirect(303, url.pathname);
    }
} satisfies Actions;
