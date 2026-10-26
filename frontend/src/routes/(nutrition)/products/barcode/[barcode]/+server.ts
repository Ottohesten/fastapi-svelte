import { ProductsService } from "$lib/client";
import { apiErrorMessage, backendLoadStatus } from "$lib/server/backend";
import { error, json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";

export const GET: RequestHandler = async ({ cookies, fetch, params }) => {
    const token = cookies.get("auth_token");
    if (!token) error(401, "Authentication required");

    try {
        const {
            data,
            error: apiError,
            response
        } = await ProductsService.GetProductByBarcode({
            auth: token,
            fetch,
            path: { barcode: params.barcode }
        });

        if (apiError || !data) {
            return json(
                { detail: apiErrorMessage(apiError, "Product lookup failed.") },
                { status: backendLoadStatus(response) }
            );
        }

        return json(data);
    } catch {
        return json({ detail: "The product service is unavailable." }, { status: 503 });
    }
};
