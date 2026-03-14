import { RecipesService, IngredientsService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";

export const load = async ({ fetch, locals, cookies }) => {
    const auth_token = cookies.get("auth_token");
    const headers = auth_token ? { Authorization: `Bearer ${auth_token}` } : undefined;

    const { data: recipes, error: recipeError } = await RecipesService.GetRecipes({
        fetch,
        headers
    });

    if (recipeError) {
        error(404, JSON.stringify(recipeError.detail));
    }

    const { data: ingredients, error: ingredientError } = await IngredientsService.GetIngredients(
        {}
    );

    if (ingredientError) {
        error(404, JSON.stringify(ingredientError.detail));
    }

    return {
        recipes: recipes,
        ingredients: ingredients,
        authenticatedUser: locals.authenticatedUser,
        scopes: locals.authenticatedUser?.scopes ?? []
    };
};
