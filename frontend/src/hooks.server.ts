import { redirect, type Handle } from '@sveltejs/kit';
import { createApiClient } from '$lib/api/api';

// define function to make api request to get user info



export const handle: Handle = async ({ event, resolve }) => {
    const auth_token = event.cookies.get("auth_token");
    // console.log(auth_token);
    // console.log(event.locals.user);


    if (!auth_token) {
        event.locals.user = null;
        return await resolve(event);
    }
    if (auth_token) {
        const client = createApiClient(event.fetch);
        const { data, error: apierror, response } = await client.GET("/users/me", {
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })
        if (data) {
            event.locals.user = data;

        }
        if (apierror) {
            console.log(apierror);
            // console.log("setting cookie to empty");
            // remove cookie
            event.cookies.set("auth_token", "", {
                httpOnly: true,
                path: '/',
                secure: true,
                // delete cookie
                maxAge: 0
            })
            // return new Response(JSON.stringify(apierror), {
            //     status: response.status,
            //     headers: {
            //         "content-type": "application/json"
            //     }
            // });
            return new Response(null, {
                status: 302,
                headers: {
                    'Location': event.url.pathname,
                    'Clear-Site-Data': '"*"'  // Forces a clean reload
                }
            });
            // return redirect(302, "/");
        }
        // console.log(event.locals.user);

    }


    const response = await resolve(event, {
        filterSerializedResponseHeaders: (name) => {
            return name === 'content-length' || name === 'content-type';
        }
    });
    return response;
};