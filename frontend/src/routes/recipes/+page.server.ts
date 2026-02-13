import { RecipesService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { redirect } from "@sveltejs/kit";

export const actions = {
    delete: async ({ fetch, params, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const recipe_id = formData.get("recipe_id") as string;
        // console.log(recipe_id);

        const { data, error: apierror } = await RecipesService.DeleteRecipe({
            auth: auth_token,
            path: { recipe_id }
        });

        if (apierror) {
            // log with file name
            console.log("apierror in recipes/page.server.ts", apierror);
            error(404, JSON.stringify(apierror.detail));
        }
    }
} satisfies Actions;
