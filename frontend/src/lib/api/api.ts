import createClient from "openapi-fetch";
import type { paths } from "./v1";
import { BACKEND_HOST } from "$env/static/private";

// export let { GET, POST, PATCH, PUT, DELETE, HEAD, TRACE } = createClient<paths>({
//     baseUrl: 'http://127.0.0.1:8000/'

// });



// Create a function that returns a client configured with the provided fetch
export const createApiClient = (customFetch: typeof fetch = fetch) => {
    console.log('baseUrl', BACKEND_HOST);
    return createClient<paths>({
        baseUrl: BACKEND_HOST,
        // baseUrl: 'http://localhost:8000/',
        fetch: customFetch
    });
};


const objectToFormData = (obj: Record<string, any>) => {
    return new URLSearchParams(
        Object.entries(obj).filter(([_, value]) => value != null)
    );
};

export const createFormApiClient = (customFetch: typeof fetch = fetch) => {
    return createClient<paths>({
        baseUrl: 'http://127.0.0.1:8000/',
        fetch: customFetch,
        // Add request transform
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        // Transform request body for POST requests
        bodySerializer: (body) => {
            return body ? objectToFormData(body) : new URLSearchParams();
        }


    });
};

// Export a default client for cases where we don't need SvelteKit's fetch
export const { GET, POST, PATCH, PUT, DELETE, HEAD, TRACE } = createApiClient();

