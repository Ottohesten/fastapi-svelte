import { redirect, type Handle } from '@sveltejs/kit';
import { createApiClient } from '$lib/api/api';
import { env } from '$env/dynamic/private';

// define function to make api request to get user info



export const handle: Handle = async ({ event, resolve }) => {
    let auth_token = event.cookies.get("auth_token");
    // console.log(auth_token);
    // console.log(event.locals.user);

    if (event.url.pathname.startsWith('/.well-known/appspecific/com.chrome.devtools')) {
        return new Response(null, { status: 204 }); // Return empty response with 204 No Content
    }


    if (!auth_token) {
        // If we have a refresh token but no access, try to refresh preemptively
        const refresh = event.cookies.get("refresh_token");
        if (refresh) {
            try {
                const refreshClient = createApiClient(event.fetch);
                const { data: refData, error: refErr } = await refreshClient.POST('/login/refresh', {
                    body: { refresh_token: refresh }
                });
                if (refData && !refErr) {
                    const newAccess = refData.access_token as string;
                    const newRefresh = (refData as any).refresh_token as string | undefined;
                    event.cookies.set('auth_token', newAccess, {
                        httpOnly: true,
                        path: '/',
                        secure: true,
                        sameSite: 'strict',
                        maxAge: 60 * 60
                    });
                    if (newRefresh) {
                        event.cookies.set('refresh_token', newRefresh, {
                            httpOnly: true,
                            path: '/',
                            secure: true,
                            sameSite: 'lax',
                            maxAge: 60 * 60 * 24 * 7
                        });
                    }
                    // continue below where we will fetch /users/me with new token
                    auth_token = newAccess;
                    console.log("Refreshed access token successfully");
                }
            } catch { }
        }
        if (!auth_token) {
            event.locals.authenticatedUser = null;
            return await resolve(event);
        }
    }

    // Try to validate current access token; on failure attempt refresh
    const client = createApiClient(event.fetch);
    let { data, error: apierror } = await client.GET("/users/me", {
        headers: { Authorization: `Bearer ${auth_token}` }
    });

    if (data) {
        event.locals.authenticatedUser = data;
    } else if (apierror) {
        // Attempt refresh using refresh_token cookie
        const refresh = event.cookies.get("refresh_token");
        if (refresh) {
            try {
                const refreshClient = createApiClient(event.fetch);
                const { data: refData, error: refErr } = await refreshClient.POST('/login/refresh', {
                    body: { refresh_token: refresh }
                });
                if (refData && !refErr) {
                    const newAccess = refData.access_token as string;
                    const newRefresh = (refData as any).refresh_token as string | undefined;
                    // Set new cookies
                    event.cookies.set('auth_token', newAccess, {
                        httpOnly: true,
                        path: '/',
                        secure: true,
                        sameSite: 'strict',
                        maxAge: 60 * 60 // 1 hour
                    });
                    if (newRefresh) {
                        event.cookies.set('refresh_token', newRefresh, {
                            httpOnly: true,
                            path: '/',
                            secure: true,
                            sameSite: 'lax',
                            maxAge: 60 * 60 * 24 * 7
                        });
                        console.log("Rotated refresh token successfully");
                    }
                    // Retry current user call
                    const retry = await client.GET('/users/me', {
                        headers: { Authorization: `Bearer ${newAccess}` }
                    });
                    if (retry.data) {
                        event.locals.authenticatedUser = retry.data;
                    } else {
                        // Failed even after refresh - fall through to logout
                        throw new Error('Failed to fetch user after refresh');
                    }
                } else {
                    throw new Error('Refresh request failed');
                }
            } catch (e) {
                // Clear cookies and redirect to login
                event.cookies.set('auth_token', '', { httpOnly: true, path: '/', secure: true, maxAge: 0 });
                event.cookies.set('refresh_token', '', { httpOnly: true, path: '/', secure: true, maxAge: 0 });
                return redirect(302, '/auth/login?redirectTo=' + event.url.pathname);
            }
        } else {
            // No refresh token - require login
            event.cookies.set('auth_token', '', { httpOnly: true, path: '/', secure: true, maxAge: 0 });
            return redirect(302, '/auth/login?redirectTo=' + event.url.pathname);
        }
    }
    const response = await resolve(event, {
        filterSerializedResponseHeaders: (name) => {
            return name === 'content-length' || name === 'content-type';
        }
    });
    return response;
};