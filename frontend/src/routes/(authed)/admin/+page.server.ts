import {
    GameService,
    IngredientsService,
    RecipesService,
    UsersService
} from "$lib/client/sdk.gen.js";
import type {
    GameSessionPublic,
    IngredientPublic,
    RecipePublic,
    UserWithPermissionsPublic
} from "$lib/client/types.gen.js";
import { loadAdminTraffic } from "$lib/server/admin-analytics";
import type { PageServerLoad } from "./$types.js";

const PAGE_SIZE = 100;
const MAX_PAGES = 1_000;

type DashboardMetric = {
    total: number | null;
    attention: number | null;
};

type PageLoader<T> = (skip: number, limit: number) => Promise<T[] | null>;

const unavailableMetric = (): DashboardMetric => ({
    total: null,
    attention: null
});

async function loadMetric<T>(
    loadPage: PageLoader<T>,
    needsAttention: (item: T) => boolean
): Promise<DashboardMetric> {
    let total = 0;
    let attention = 0;

    try {
        for (let page = 0; page < MAX_PAGES; page += 1) {
            const items = await loadPage(page * PAGE_SIZE, PAGE_SIZE);
            if (!items) return unavailableMetric();

            total += items.length;
            attention += items.filter(needsAttention).length;

            if (items.length < PAGE_SIZE) {
                return { total, attention };
            }
        }
    } catch {
        return unavailableMetric();
    }

    // Avoid returning a misleading partial count if the collection is unexpectedly huge.
    return unavailableMetric();
}

export const load: PageServerLoad = async ({ cookies, request }) => {
    const authToken = cookies.get("auth_token");

    const [users, recipes, ingredients, sessions, traffic] = await Promise.all([
        loadMetric<UserWithPermissionsPublic>(
            async (skip, limit) => {
                if (!authToken) return null;

                const { data, error } = await UsersService.GetUsersWithPermissions({
                    auth: authToken,
                    query: { skip, limit }
                });
                return error || !data ? null : data.data;
            },
            (user) => user.is_active === false
        ),
        loadMetric<RecipePublic>(
            async (skip, limit) => {
                const { data, error } = await RecipesService.GetRecipes({
                    auth: authToken,
                    query: { skip, limit }
                });
                return error || !data ? null : data;
            },
            (recipe) => recipe.is_hidden === true
        ),
        loadMetric<IngredientPublic>(
            async (skip, limit) => {
                const { data, error } = await IngredientsService.GetIngredients({
                    query: { skip, limit }
                });
                return error || !data ? null : data;
            },
            (ingredient) => !ingredient.barcode
        ),
        loadMetric<GameSessionPublic>(
            async (skip, limit) => {
                const { data, error } = await GameService.GetGameSessions({
                    query: { skip, limit }
                });
                return error || !data ? null : data;
            },
            (session) => session.players.length === 0
        ),
        loadAdminTraffic(authToken, { signal: request.signal })
    ]);

    return {
        metrics: {
            users,
            recipes,
            ingredients,
            sessions
        },
        traffic
    };
};
