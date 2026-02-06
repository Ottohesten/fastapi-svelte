import { createApiClient } from "$lib/api/api";
import { redirect } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { z } from "zod";
import { message, superValidate, fail } from "sveltekit-superforms";
import { error } from "@sveltejs/kit";
import { RecipeSchema } from "$lib/schemas/schemas.js";
import { env } from "$env/dynamic/private";

export const load = async ({ fetch, parent, cookies }) => {
    const client = createApiClient(fetch);
    const auth_token = cookies.get("auth_token");

    if (!auth_token) {
        redirect(302, "/auth/login");
    }

    // get the list of available ingredients
    const { data: ingredients, error: apierror, response } = await client.GET("/ingredients/");

    if (apierror) {
        return error(404, JSON.stringify(apierror.detail));
    }

    const form = await superValidate(zod(RecipeSchema));
    // const form = await superValidate({ ingredients: ingredients }, zod(RecipeSchema));
    return {
        ingredients: ingredients,
        form,
        backendUrl: env.BACKEND_HOST || "http://127.0.0.1:8000"
    };
};

export const actions = {
    default: async ({ fetch, request, cookies }) => {
        const form = await superValidate(request, zod(RecipeSchema));

        if (!form.valid) {
            return fail(400, { form });
        }
        // return message(form, 'You have uploaded a valid file!');
        // return setError(form, 'image', 'Could not process file.');

        // post form data to the API
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        // Transform ingredients from frontend format to backend format
        const ingredientsForBackend = form.data.ingredients.map((ingredient) => ({
            ingredient_id: ingredient.id,
            amount: ingredient.amount,
            unit: ingredient.unit
        }));

        let imageUrl = null;
        if (form.data.image instanceof File && form.data.image.size > 0) {
            const formData = new FormData();
            formData.append("file", form.data.image);

            // Upload image
            const { data: uploadData, error: uploadError } = await client.POST(
                "/recipes/upload-image",
                {
                    body: formData as any, // Type cast might be needed if OpenAPI client doesn't support FormData directly yet or generated types are strict
                    headers: {
                        Authorization: `Bearer ${auth_token}`
                    }
                }
            );

            if (uploadError) {
                return fail(400, { form, error: "Failed to upload image" });
            }

            if (uploadData) {
                imageUrl = (uploadData as { url: string }).url;
            }
        }

        const {
            data,
            error: apierror,
            response
        } = await client.POST("/recipes/", {
            body: {
                title: form.data.title,
                instructions: form.data.instructions ?? null,
                ingredients: ingredientsForBackend,
                servings: form.data.servings,
                image: imageUrl
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (apierror) {
            return fail(400, { form });
        }

        return redirect(302, "/recipes");
        // return message(form, "Form posted successfully!");
    }
} satisfies Actions;
