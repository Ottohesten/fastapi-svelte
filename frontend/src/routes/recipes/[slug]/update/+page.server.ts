import { IngredientsService, RecipesService } from "$lib/client/sdk.gen.js";
import { redirect } from "@sveltejs/kit";
import { error } from "@sveltejs/kit";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { z } from "zod";
import { message, superValidate, fail } from "sveltekit-superforms";
import type { Actions } from "./$types.js";
import { RecipeSchema } from "$lib/schemas/schemas.js";

export async function load({ fetch, params, locals, request, parent, url }) {
    const { authenticatedUser } = locals;
    const parent_data = await parent();

    // if there is no user redirect to login page
    if (!authenticatedUser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

    // if user is not superuser, or is not the owner of the recipe, return 403 forbidden
    if (!authenticatedUser?.is_superuser && !parent_data.is_owner) {
        error(403, "Forbidden");
    }

    // Get the list of available ingredients
    const { data: allIngredients, error: apierror } = await IngredientsService.GetIngredients({
        fetch
    });

    if (apierror) {
        return error(404, JSON.stringify(apierror.detail));
    }

    // Transform the backend ingredient_links to frontend ingredients format
    const frontendIngredients = parent_data.recipe.ingredient_links.map((link) => ({
        id: link.ingredient.id,
        title: link.ingredient.title, // Include title for display
        amount: link.amount,
        unit: link.unit as "g" | "kg" | "ml" | "L" | "pcs"
    }));

    const form = await superValidate(
        {
            ingredients: frontendIngredients,
            title: parent_data.recipe.title,
            instructions: parent_data.recipe.instructions ?? undefined,
            servings: parent_data.recipe.servings ?? 1
        },
        zod(RecipeSchema)
    );

    return {
        // Pass all ingredients - the frontend will filter them reactively
        ingredients: allIngredients,
        form
    };
}

export const actions = {
    default: async ({ fetch, request, cookies, params, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(303, `/auth/login?redirectTo=${url.pathname}`);
        }

        const form = await superValidate(request, zod(RecipeSchema));
        if (!form.valid) {
            return fail(400, { form });
        }

        // Transform ingredients from frontend format to backend format
        const ingredientsForBackend = form.data.ingredients.map((ingredient) => ({
            ingredient_id: ingredient.id,
            amount: ingredient.amount,
            unit: ingredient.unit
        }));

        let imageUrl = undefined;
        if (form.data.image instanceof File && form.data.image.size > 0) {
            const formData = new FormData();
            formData.append("file", form.data.image);

            // Upload image
            const { data: uploadData, error: uploadError } = await RecipesService.UploadRecipeImage(
                {
                    fetch,
                    auth: auth_token,
                    body: formData as any
                }
            );

            if (uploadError) {
                return fail(400, { form, error: "Failed to upload image" });
            }

            if (uploadData) {
                imageUrl = (uploadData as { url: string }).url;
            }
        } else if (form.data.clearImage) {
            imageUrl = null;
        }

        // post form data to the API (when backend PATCH is implemented)
        const recipe_id = params.slug;
        const { data, error: apierror } = await RecipesService.UpdateRecipe({
            auth: auth_token,
            body: {
                title: form.data.title,
                instructions: form.data.instructions ?? null,
                ingredients: ingredientsForBackend,
                servings: form.data.servings,
                image: imageUrl
            },
            path: { recipe_id }
        });

        if (apierror) {
            return fail(400, { form });
        }

        // Redirect to the recipes page
        redirect(302, "/recipes");
    }
} satisfies Actions;
