import { IngredientsService, RecipesService } from "$lib/client/sdk.gen.js";
import { redirect } from "@sveltejs/kit";
import type { Actions } from "./$types.js";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { superValidate, fail } from "sveltekit-superforms";
import { error } from "@sveltejs/kit";
import { RecipeSchema } from "$lib/schemas/schemas.js";

export const load = async ({ fetch, parent, cookies, url }) => {
    const auth_token = cookies.get("auth_token");
    if (!auth_token) redirect(302, `/auth/login?redirectTo=${url.pathname}`);

    // get the list of available ingredients
    const {
        data: ingredients,
        error: apierror,
        response
    } = await IngredientsService.GetIngredients({});

    if (apierror) {
        return error(404, JSON.stringify(apierror.detail));
    }

    const { data: recipes, error: recipeError } = await RecipesService.GetRecipes({});
    if (recipeError) {
        return error(404, JSON.stringify(recipeError.detail));
    }

    const form = await superValidate(zod(RecipeSchema));
    return {
        ingredients: ingredients,
        recipes: recipes,
        form
    };
};

export const actions = {
    default: async ({ fetch, request, cookies, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) redirect(302, `/auth/login?redirectTo=${url.pathname}`);

        const form = await superValidate(request, zod(RecipeSchema));
        if (!form.valid) return fail(400, { form });

        // Transform ingredients from frontend format to backend format
        const ingredientsForBackend = form.data.ingredients.map((ingredient) => ({
            ingredient_id: ingredient.id,
            amount: ingredient.amount,
            unit: ingredient.unit
        }));
        const subRecipesForBackend = form.data.sub_recipes.map((recipe) => ({
            sub_recipe_id: recipe.id,
            scale_factor: recipe.scale_factor
        }));

        let imageUrl = null;
        if (form.data.image instanceof File && form.data.image.size > 0) {
            const formData = new FormData();
            formData.append("file", form.data.image);

            // Upload image
            const { data: uploadData, error: uploadError } = await RecipesService.UploadRecipeImage(
                {
                    auth: auth_token,
                    body: formData as any // Type cast might be needed if OpenAPI client doesn't support FormData directly yet or generated types are strict
                }
            );

            if (uploadError) {
                return fail(400, { form, error: "Failed to upload image" });
            }

            if (uploadData) {
                imageUrl = (uploadData as { url: string }).url;
            }
        }

        const { data, error: apierror } = await RecipesService.CreateRecipe({
            auth: auth_token,
            body: {
                title: form.data.title,
                instructions: form.data.instructions ?? null,
                ingredients: ingredientsForBackend,
                sub_recipes: subRecipesForBackend,
                servings: form.data.servings,
                image: imageUrl
            }
        });

        if (apierror) {
            return fail(400, { form });
        }

        return redirect(302, "/recipes");
        // return message(form, "Form posted successfully!");
    }
} satisfies Actions;
