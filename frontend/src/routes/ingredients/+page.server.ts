import { IngredientsService } from "$lib/client/sdk.gen.js";
import { error, redirect } from "@sveltejs/kit";
import { message, superValidate, fail } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import type { Actions } from "./$types.js";
import { IngredientSchema } from "$lib/schemas/schemas.js";

export const load = async ({ fetch, locals }) => {
    const { data, error: apierror, response } = await IngredientsService.GetIngredients({});

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }

    return {
        ingredients: data,
        ingredientCreateForm: await superValidate(zod(IngredientSchema))
    };
};

export const actions = {
    create: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const form = await superValidate(request, zod(IngredientSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        const { error: apierror } = await IngredientsService.CreateIngredient({
            auth: () => auth_token,
            body: form.data
        });

        if (apierror) {
            return message(
                form,
                "Failed to create ingredient: " + JSON.stringify(apierror.detail),
                {
                    status: 400
                }
            );
        }

        return message(form, "Ingredient created successfully!");
    },
    delete: async ({ fetch, params, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const ingredient_id = formData.get("ingredient_id") as string;

        const { error: apierror } = await IngredientsService.DeleteIngredient({
            auth: () => auth_token,
            path: { ingredient_id }
        });

        if (apierror) {
            error(400, JSON.stringify(apierror.detail));
        }
    }
} satisfies Actions;
