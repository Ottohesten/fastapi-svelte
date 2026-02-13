import { IngredientsService } from "$lib/client/sdk.gen.js";
import { error, fail, redirect } from "@sveltejs/kit";
import { message, superValidate } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import type { Actions } from "./$types.js";
import { IngredientSchema, IngredientUpdateSchema } from "$lib/schemas/schemas.js";

export const load = async ({ fetch, locals }) => {
    const { data, error: apierror, response } = await IngredientsService.GetIngredients({});

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }

    return {
        ingredients: data,
        ingredientCreateForm: await superValidate(zod(IngredientSchema), {
            id: "ingredientCreateForm"
        }),
        ingredientUpdateForm: await superValidate(zod(IngredientUpdateSchema), {
            id: "ingredientUpdateForm"
        })
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

        const { data, error: apierror } = await IngredientsService.CreateIngredient({
            auth: auth_token,
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
    update: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const form = await superValidate(request, zod(IngredientUpdateSchema));
        if (!form.valid) {
            return fail(400, { form });
        }

        const { id, ...updateData } = form.data;

        const { error: apierror } = await IngredientsService.UpdateIngredient({
            auth: auth_token,
            path: { ingredient_id: id },
            body: updateData
        });

        if (apierror) {
            return message(
                form,
                "Failed to update ingredient: " + JSON.stringify(apierror.detail),
                {
                    status: 400
                }
            );
        }

        return message(form, "Ingredient updated successfully!");
    },
    delete: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const ingredient_id = formData.get("id") as string;

        if (!ingredient_id) {
            return fail(400, { error: "Ingredient ID is required" });
        }

        const { error: apierror } = await IngredientsService.DeleteIngredient({
            auth: auth_token,
            path: { ingredient_id: ingredient_id }
        });

        if (apierror) {
            return fail(400, { error: "Failed to delete ingredient" });
        }

        return { success: true };
    }
} satisfies Actions;
