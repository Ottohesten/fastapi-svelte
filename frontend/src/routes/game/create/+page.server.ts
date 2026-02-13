import { GameService } from "$lib/client/sdk.gen.js";
import { redirect } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { z } from "zod";
import { message, superValidate, fail } from "sveltekit-superforms";
import { error } from "@sveltejs/kit";
import { GameSessionSchema } from "$lib/schemas/schemas.js";

export const load = async ({ fetch, parent }) => {
    const form = await superValidate(zod(GameSessionSchema));

    return {
        form
    };
};

export const actions = {
    default: async ({ fetch, request, cookies, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }
        const form = await superValidate(request, zod(GameSessionSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        const { data, error: apierror } = await GameService.CreateGameSession({
            auth: auth_token,
            body: {
                title: form.data.title,
                teams: form.data.teams.map((team) => {
                    return {
                        name: team.name
                    };
                })
            }
        });

        if (apierror) {
            return message(form, `Error: ${apierror.detail}`);
        }

        // return redirect(302, `/game/${data.id}`);
        return redirect(302, "/game/");
    }
} satisfies Actions;
