import { GameService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { z } from "zod";
import { message, superValidate, fail } from "sveltekit-superforms";
import { GameSessionAddDrinkSchema } from "$lib/schemas/schemas.js";

export const load = async ({}) => {
    const addDrinkForm = await superValidate(zod(GameSessionAddDrinkSchema), {
        id: "addDrinkForm"
    });

    return {
        addDrinkForm
    };
};

export const actions = {
    addDrinkToPlayer: async ({ fetch, params, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const form = await superValidate(request, zod(GameSessionAddDrinkSchema));
        if (!form.valid) {
            return fail(400, { form });
        }

        const { player_id, drink_id, amount } = form.data;

        const { data, error: apierror } = await GameService.AddDrinkToPlayer({
            auth: () => auth_token,
            body: {
                drink_id: drink_id,
                amount: amount
            },
            path: {
                game_player_id: player_id,
                game_session_id: params.game_session_id
            }
        });

        if (apierror) {
            return message(form, JSON.stringify(apierror.detail), { status: 400 });
        }

        return message(form, "Drink added successfully");
    }
} satisfies Actions;
