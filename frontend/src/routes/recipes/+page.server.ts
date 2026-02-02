import { createApiClient } from "$lib/api/api";
import { error } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { redirect } from "@sveltejs/kit";
import { fail } from "@sveltejs/kit";

export const actions = {
	delete: async ({ fetch, params, cookies, request }) => {
		const client = createApiClient(fetch);
		const auth_token = cookies.get("auth_token");

		if (!auth_token) {
			redirect(302, "/auth/login");
		}

		const formData = await request.formData();
		const recipe_id = formData.get("recipe_id") as string;
		// console.log(recipe_id);

		const { error: apierror, response } = await client.DELETE("/recipes/{recipe_id}", {
			params: {
				path: { recipe_id: recipe_id }
			},
			headers: {
				Authorization: `Bearer ${auth_token}`
			}
		});

		if (apierror) {
			// log with file name
			console.log("apierror in recipes/page.server.ts", apierror);
			error(404, JSON.stringify(apierror.detail));
		}

		// return redirect(302, "/recipes");
	}
} satisfies Actions;
