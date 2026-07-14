import { IngredientsService } from "$lib/client/sdk.gen.js";
import { error, json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types.js";

export const GET: RequestHandler = async ({ cookies, params }) => {
    const authToken = cookies.get("auth_token");
    if (!authToken) error(401, "Authentication required");

    const {
        data,
        error: apiError,
        response
    } = await IngredientsService.GetIngredientByBarcode({
        auth: authToken,
        path: { barcode: params.barcode }
    });

    if (apiError || !data) {
        const detail =
            apiError && typeof apiError === "object" && "detail" in apiError
                ? String(apiError.detail)
                : "Product lookup failed";
        return json({ detail }, { status: response?.status ?? 502 });
    }

    return json(data);
};
