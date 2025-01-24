import { createApiClient } from '$lib/api/api';
import { redirect } from '@sveltejs/kit';
import { fail } from "@sveltejs/kit";
import type { Actions } from './$types.js';
import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';
import { message, superValidate } from 'sveltekit-superforms';

const RecipeSchema = z.object({
    title: z.string(),
    // mpt optional
    description: z.string().optional(),
});

export const load = async ({ }) => {
    const form = await superValidate(zod(RecipeSchema));


    return { form };
}


export const actions = {
    default: async ({ fetch, request, cookies }) => {
        // const formData = await request.formData();

        // const errors: Record<string, unknown> = {}

        // if (!formData.get("title")) {
        //     errors.title = "Title is required";
        // }

        // if (!formData.get("description")) {
        //     errors.description = "Description is required";
        // }
        // if (Object.keys(errors).length > 0) {
        //     const data = {
        //         data: Object.fromEntries(formData),
        //         errors
        //     }
        //     return fail(422, data)
        // }
        // return redirect(302, "/recipes");

        const form = await superValidate(request, zod(RecipeSchema));
        console.log(form)
        if (!form.valid) {
            return fail(400, { form });
        }

        // post form data to the API
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");
        const { data, error: apierror, response } = await client.POST("/recipes/", {
            body: {
                title: form.data.title,
                description: form.data.description,
                ingredients: [],
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }

        })



        return redirect(302, "/recipes");
        // return message(form, "Form posted successfully!");
    }
} satisfies Actions;