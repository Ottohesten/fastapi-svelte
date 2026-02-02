import { createApiClient } from "$lib/api/api";
import { error } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";
import { env } from "$env/dynamic/private";

export const load = async ({ fetch, params, locals }) => {
	const client = createApiClient(fetch);

	const {
		data,
		error: apierror,
		response
	} = await client.GET("/game/{game_session_id}", {
		params: {
			path: { game_session_id: params.game_session_id }
		}
	});

	if (apierror) {
		error(response.status, apierror.detail?.toString());
	}

	const {
		data: drinks,
		error: drinksError,
		response: drinksResponse
	} = await client.GET("/game/drinks");

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
