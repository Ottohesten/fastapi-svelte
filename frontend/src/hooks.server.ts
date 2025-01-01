import type { Handle } from '@sveltejs/kit';
import { createApiClient } from '$lib/api/api';

// define function to make api request to get user info



export const handle: Handle = async ({ event, resolve }) => {
    const auth_token = event.cookies.get("auth_token");
    if (auth_token) {
        const client = createApiClient(event.fetch);
        const { data, error: apierror, response } = await client.GET("/users/me", {
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })
        if (apierror) {
            console.log(apierror);
            return new Response(JSON.stringify(apierror), {
                status: response.status,
                headers: {
                    "content-type": "application/json"
                }
            });
        }
        event.locals.user = data;
    }


    const response = await resolve(event, {
        filterSerializedResponseHeaders: (name) => {
            return name === 'content-length' || name === 'content-type';
        }
    });
    return response;
};