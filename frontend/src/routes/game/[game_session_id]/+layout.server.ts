import { GameService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";
import { env } from "$env/dynamic/private";

export const load = async ({ fetch, params, locals }) => {
    const {
        data,
        error: apierror,
        response
    } = await GameService.GetGameSession({
        path: { game_session_id: params.game_session_id }
    });

    if (apierror) {
        error(response.status, apierror.detail?.toString());
    }

    const {
        data: drinks,
        error: drinksError,
        response: drinksResponse
    } = await GameService.GetDrinks();

    if (drinksError) {
        error(drinksResponse.status, drinksError.detail?.toString());
    }

    return {
        game_session: data,
        drinks: drinks,
        is_owner: locals.authenticatedUser ? data.owner.id === locals.authenticatedUser.id : false,
        backendHost: env.BACKEND_HOST || "http://127.0.0.1:8000"
    };
};
