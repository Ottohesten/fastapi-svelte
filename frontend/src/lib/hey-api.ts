import type { CreateClientConfig } from "$lib/client/client.gen";
import { env } from "$env/dynamic/private";

export const createClientConfig: CreateClientConfig = (config) => ({
    ...config,
    // auth: auth_token,
    baseUrl: env.BACKEND_HOST || "http://127.0.0.1:8000"

    // headers: {
    //     ...config?.headers,
    //     "Authorization": "Bearer "
    // }
});
