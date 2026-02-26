import { env } from "$env/dynamic/private";
import { LoginService } from "$lib/client";
import { redirect, type Handle } from "@sveltejs/kit";
import jwt, { type JwtPayload } from "jsonwebtoken";

type AccessTokenPayload = JwtPayload & {
    sub?: string;
    uid?: string;
    scopes?: unknown;
    is_active?: unknown;
    is_superuser?: unknown;
    full_name?: unknown;
};

type HandleEvent = Parameters<Handle>[0]["event"];

const ACCESS_COOKIE_MAX_AGE = 60 * 60;
const REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;

function setSessionCookies(
    event: HandleEvent,
    accessToken: string,
    refreshToken?: string | undefined
) {
    event.cookies.set("auth_token", accessToken, {
        httpOnly: true,
        path: "/",
        secure: true,
        sameSite: "strict",
        maxAge: ACCESS_COOKIE_MAX_AGE
    });

    if (refreshToken) {
        event.cookies.set("refresh_token", refreshToken, {
            httpOnly: true,
            path: "/",
            secure: true,
            sameSite: "lax",
            maxAge: REFRESH_COOKIE_MAX_AGE
        });
    }
}

function clearSessionCookies(event: HandleEvent) {
    event.cookies.set("auth_token", "", {
        httpOnly: true,
        path: "/",
        secure: true,
        maxAge: 0
    });
    event.cookies.set("refresh_token", "", {
        httpOnly: true,
        path: "/",
        secure: true,
        maxAge: 0
    });
}

function decodeAccessToken(token: string): AccessTokenPayload | null {
    try {
        if (env.SECRET_KEY) {
            const verified = jwt.verify(token, env.SECRET_KEY);
            return typeof verified === "string" ? null : (verified as AccessTokenPayload);
        }
        const decoded = jwt.decode(token);
        return decoded && typeof decoded !== "string" ? (decoded as AccessTokenPayload) : null;
    } catch {
        return null;
    }
}

function isExpired(payload: AccessTokenPayload): boolean {
    if (typeof payload.exp !== "number") return true;
    const now = Math.floor(Date.now() / 1000);
    return payload.exp <= now;
}

function hasRequiredClaims(payload: AccessTokenPayload): payload is AccessTokenPayload & {
    sub: string;
    uid: string;
    is_active: boolean;
    is_superuser: boolean;
    scopes: unknown[];
} {
    return (
        typeof payload.sub === "string" &&
        typeof payload.uid === "string" &&
        typeof payload.is_active === "boolean" &&
        typeof payload.is_superuser === "boolean" &&
        Array.isArray(payload.scopes)
    );
}

async function refreshAccessToken(event: HandleEvent): Promise<string | undefined> {
    const refresh = event.cookies.get("refresh_token");
    if (!refresh) return undefined;

    try {
        const { data, error } = await LoginService.RefreshAccessToken({
            body: { refresh_token: refresh }
        });

        if (!data || error) return undefined;

        const accessToken = data.access_token as string;
        const rotatedRefresh = (data as { refresh_token?: string | null }).refresh_token;
        setSessionCookies(event, accessToken, rotatedRefresh ?? undefined);
        return accessToken;
    } catch {
        return undefined;
    }
}

function hydrateLocalsFromToken(event: HandleEvent, payload: AccessTokenPayload) {
    const scopes = Array.isArray(payload.scopes)
        ? payload.scopes.filter((scope): scope is string => typeof scope === "string")
        : [];
    const full_name =
        typeof payload.full_name === "string" || payload.full_name === null
            ? payload.full_name
            : null;

    event.locals.authenticatedUser = {
        id: payload.uid as string,
        email: payload.sub as string,
        is_active: payload.is_active as boolean,
        is_superuser: payload.is_superuser as boolean,
        full_name,
        scopes
    };
}

export const handle: Handle = async ({ event, resolve }) => {
    if (event.url.pathname.startsWith("/.well-known/appspecific/com.chrome.devtools")) {
        return new Response(null, { status: 204 });
    }

    const hadAuthToken = Boolean(event.cookies.get("auth_token"));
    let authToken = event.cookies.get("auth_token");
    let payload = authToken ? decodeAccessToken(authToken) : null;

    if (!authToken || !payload || isExpired(payload) || !hasRequiredClaims(payload)) {
        authToken = await refreshAccessToken(event);
        payload = authToken ? decodeAccessToken(authToken) : null;
    }

    if (authToken && payload && !isExpired(payload) && hasRequiredClaims(payload)) {
        hydrateLocalsFromToken(event, payload);
    } else {
        event.locals.authenticatedUser = null;

        if (event.cookies.get("auth_token") || event.cookies.get("refresh_token")) {
            clearSessionCookies(event);
            if (hadAuthToken) {
                return redirect(302, "/auth/login?redirectTo=" + event.url.pathname);
            }
        }
    }

    const response = await resolve(event, {
        filterSerializedResponseHeaders: (name) => {
            return name === "content-length" || name === "content-type";
        }
    });

    return response;
};
