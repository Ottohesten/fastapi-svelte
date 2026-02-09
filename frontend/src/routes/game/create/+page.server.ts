import { createApiClient } from "$lib/api/api";
import { redirect } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { z } from "zod";
import { message, superValidate, fail } from "sveltekit-superforms";
import { error } from "@sveltejs/kit";
import { GameSessionSchema } from "$lib/schemas/schemas.js";

export const load = async ({ fetch, parent }) => {
    // const client = createApiClient(fetch);

    const form = await superValidate(zod(GameSessionSchema));

    return {
        form
    };
};

export const actions = {
    default: async ({ fetch, request, cookies, url }) => {
        const auth_token = cookies.get("auth_token");
        const form = await superValidate(request, zod(GameSessionSchema));
        // console.log(form)
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        if (!form.valid) {
            return fail(400, { form });
        }

        const client = createApiClient(fetch);

        const {
            data,
            error: apierror,
            response
        } = await client.POST("/game/", {
            body: {
                title: form.data.title,
                teams: form.data.teams.map((team) => {
                    return {
                        name: team.name
                        // players: (team.players ?? []).map((player) => {
                        //     return {
                        //         name: player.name
                        //     }
                        // })
                    };
                })
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            // console.log("apierror in game/create/+page.server.ts", apierror);
            // return error(404, JSON.stringify(apierror.detail));
            return message(form, `Error: ${apierror.detail}`);
        }

        // return redirect(302, `/game/${data.id}`);
        return redirect(302, "/game/");
    }
} satisfies Actions;
