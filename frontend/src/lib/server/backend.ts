import { redirect, type Cookies } from "@sveltejs/kit";

export type BackendActionStatus = 400 | 401 | 403 | 404 | 409 | 422 | 503;

export function requireAuthToken(cookies: Pick<Cookies, "get">, returnTo: string): string {
    const token = cookies.get("auth_token");
    if (!token) redirect(303, `/auth/login?redirectTo=${encodeURIComponent(returnTo)}`);
    return token;
}

export function apiErrorMessage(apiError: unknown, fallback: string): string {
    if (!apiError || typeof apiError !== "object" || !("detail" in apiError)) return fallback;

    const detail = apiError.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        const messages = detail.flatMap((item) => {
            if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
                return [item.msg];
            }
            return [];
        });
        if (messages.length) return messages.join("; ");
    }
    return fallback;
}

export function backendActionStatus(response: Response | undefined): BackendActionStatus {
    const status = response?.status ?? 400;
    return [400, 401, 403, 404, 409, 422, 503].includes(status)
        ? (status as BackendActionStatus)
        : 400;
}

export function backendLoadStatus(response: Response | undefined): number {
    const status = response?.status ?? 502;
    return status >= 400 && status <= 599 ? status : 502;
}

/**
 * The generated client types OpenAPI `date` values as Date, but FastAPI's date-only wire format
 * is YYYY-MM-DD. This keeps the exact string at runtime while satisfying the generated boundary.
 */
export function wireDate(value: string): Date {
    return value as unknown as Date;
}
