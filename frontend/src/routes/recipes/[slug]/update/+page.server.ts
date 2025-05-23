import { redirect } from '@sveltejs/kit';
import { error } from '@sveltejs/kit';
import { createApiClient } from '$lib/api/api.js';
// import { createApiClient } from '$lib/api/api';
import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate, fail } from 'sveltekit-superforms';
import type { Actions } from './$types.js';
import { RecipeSchema } from '$lib/schemas/schemas.js';


export async function load({ fetch, params, locals, request, parent, url }) {
    const { authenticatedUser } = locals;
    // const client = createApiClient(fetch);

    // const { data, error: apierror, response } = await client.GET("/recipes/{recipe_id}", {
    //     params: {
    //         path: { recipe_id: params.slug }
    //     }
    // })
    // console.log(data)
    // console.log(parent)
    // console.log(request)
    const recipe_id = params.slug
    const parent_data = await parent()


    // if there is no user redirect to login page
    if (!authenticatedUser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

    // if user is not superuser, or is not the owner of the recipe, return 403 forbidden
    if (!authenticatedUser?.is_superuser && !parent_data.is_owner) {
        error(403, "Forbidden");
    }


    // const form = await superValidate({ ingredients: parent_data.recipe.ingredients }, zod(RecipeSchema));
    const form = await superValidate({ ingredients: parent_data.recipe.ingredients, title: parent_data.recipe.title, instructions: parent_data.recipe.instructions ?? undefined }, zod(RecipeSchema));
    // const form = await superValidate(parent_data.recipe, zod(RecipeSchema));

    return {
        form
    }

}


export const actions = {
    default: async ({ fetch, request, cookies, params }) => {
        const form = await superValidate(request, zod(RecipeSchema));
        console.log(form)
        if (!form.valid) {
            return fail(400, { form });
        }
        // return message(form, 'You have uploaded a valid file!');
        // return setError(form, 'image', 'Could not process file.');

        // post form data to the API
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");
        const { data, error: apierror, response } = await client.PATCH("/recipes/{recipe_id}", {
            params: {
                path: { recipe_id: params.slug }
            },
            body: form.data,

            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            console.log("apierror in recipes/[slug]/update/[page.server.ts file", apierror);
            error(404, JSON.stringify(apierror.detail));
        }


        return redirect(302, "/recipes");
        // return message(form, "Form posted successfully!");
    }
} satisfies Actions;
