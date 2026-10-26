import type { CreateClientConfig } from "#lib/client/client.gen.js";
import * as env from "$app/env/private";

export const createClientConfig: CreateClientConfig = (config) => ({
    ...config,
    // auth: auth_token,
    baseUrl: env.BACKEND_HOST || "http://127.0.0.1:8000"

    // headers: {
    //     ...config?.headers,
    //     "Authorization": "Bearer "
    // }
});
