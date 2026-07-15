import { env } from "$env/dynamic/private";
import { parsePageMetricBatch } from "$lib/observability/page-metrics";
import type { RequestHandler } from "./$types";

const MAX_REQUEST_BYTES = 4_096;
const FORWARD_TIMEOUT_MS = 3_000;

export const POST: RequestHandler = async ({ fetch, locals, request, url }) => {
    if (request.headers.get("content-type")?.split(";", 1)[0] !== "application/json") {
        return new Response(null, { status: 415 });
    }

    const origin = request.headers.get("origin");
    const fetchSite = request.headers.get("sec-fetch-site");
    if (origin !== url.origin || (fetchSite && fetchSite !== "same-origin")) {
        return new Response(null, { status: 403 });
    }

    const declaredLength = Number(request.headers.get("content-length"));
    if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
        return new Response(null, { status: 413 });
    }

    let rawBody: string;
    try {
        rawBody = await request.text();
    } catch {
        return new Response(null, { status: 400 });
    }

    if (new TextEncoder().encode(rawBody).byteLength > MAX_REQUEST_BYTES) {
        return new Response(null, { status: 413 });
    }

    let rawBatch: unknown;
    try {
        rawBatch = JSON.parse(rawBody);
    } catch {
        return new Response(null, { status: 400 });
    }

    const batch = parsePageMetricBatch(rawBatch);
    if (!batch) {
        return new Response(null, { status: 400 });
    }

    const ingestToken = env.ANALYTICS_INGEST_TOKEN;
    if (!ingestToken) {
        return new Response(null, { status: 204 });
    }

    const authenticated = Boolean(locals.authenticatedUser);
    const body = JSON.stringify({
        events: batch.events.map(({ metric, route }) => ({ metric, route, authenticated }))
    });
    const backendHost = (env.BACKEND_HOST || "http://127.0.0.1:8000").replace(/\/$/, "");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), FORWARD_TIMEOUT_MS);

    try {
        const response = await fetch(`${backendHost}/analytics/events`, {
            method: "POST",
            headers: {
                "content-type": "application/json",
                "x-analytics-ingest-token": ingestToken
            },
            body,
            signal: controller.signal
        });
        if (!response.ok) {
            console.warn("Analytics forwarding returned a non-success status", response.status);
        }
    } catch (error) {
        // The client intentionally receives no upstream error details.
        console.warn(
            "Analytics forwarding failed",
            error instanceof Error ? error.name : "UnknownError"
        );
    } finally {
        clearTimeout(timeout);
    }

    return new Response(null, { status: 204 });
};
