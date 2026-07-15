import { json } from "@sveltejs/kit";
import { loadAdminTraffic } from "$lib/server/admin-analytics";
import type { RequestHandler } from "./$types.js";

export const GET: RequestHandler = async ({ cookies, locals, request }) => {
    if (!locals.authenticatedUser) {
        return json({ detail: "Not authenticated" }, { status: 401 });
    }
    if (!locals.authenticatedUser.is_superuser) {
        return json({ detail: "Forbidden" }, { status: 403 });
    }

    const traffic = await loadAdminTraffic(cookies.get("auth_token"), {
        signal: request.signal
    });
    if (!traffic) {
        return json(
            { detail: "Traffic data is temporarily unavailable" },
            { status: 503, headers: { "cache-control": "private, no-store" } }
        );
    }

    return json(traffic, {
        headers: { "cache-control": "private, no-store" }
    });
};
