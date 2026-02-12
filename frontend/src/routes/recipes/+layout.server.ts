import { RecipesService, IngredientsService } from "$lib/client/sdk.gen.js";
import { error } from "@sveltejs/kit";

export const load = async ({ fetch, locals }) => {
    const { data: recipes, error: recipeError } = await RecipesService.ReadRecipes({});

    if (recipeError) {
        error(404, JSON.stringify(recipeError.detail));
    }

    const { data: ingredients, error: ingredientError } = await IngredientsService.ReadIngredients(
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
