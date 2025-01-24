import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import type { Actions } from './$types.js';
import { redirect } from '@sveltejs/kit';
import { fail } from '@sveltejs/kit';


export const actions = {
    delete: async ({ fetch, params, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

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
        })

        return redirect(302, "/recipes");

    },
    // default: async ({ fetch, cookies, request }) => {
    //     // const client = createApiClient(fetch);
    //     // const auth_token = cookies.get("auth_token");

    //     const formData = await request.formData();
    //     console.log(formData);

    //     // error for testing purposes
    //     // return error(500, "Internal Server Error");

    //     // return success
    //     const errors: Record<string, unknown> = {}

    //     if (!formData.get("title")) {
    //         errors.title = "Title is required";
    //     }

    //     if (!formData.get("description")) {
    //         errors.description = "Description is required";
    //     }

    //     return fail(422, {
    //         data: Object.fromEntries(formData),
    //         errors: errors
    //     })







    //     // const { data, error: apierror, response } = await client.POST("/recipes/", {
    //     //     body: {

    //     //     }
    //     // })
    // }
    // create: async ({ fetch, cookies, request, params, url }) => {
    //     const formData = await request.formData();
    //     console.log(formData);

    //     const errors: Record<string, unknown> = {}

    //     if (!formData.get("title")) {
    //         errors.title = "Title is required";
    //     }

    //     if (!formData.get("description")) {
    //         errors.description = "Description is required";
    //     }

    //     // return fail(422, {
    //     //     data: Object.fromEntries(formData),
    //     //     errors: errors
    //     // })

    //     if (Object.keys(errors).length > 0) {
    //         const data = {
    //             data: Object.fromEntries(formData),
    //             errors
    //         }
    //         console.log(data)
    //         return fail(422, data)
    //     }

    //     // return a success message and redirect
    //     return redirect(302, "/recipes");
    // }
} satisfies Actions;

