import type { CreateClientConfig } from "$lib/client/client.gen";
import { env } from "$env/dynamic/private";

export const createClientConfig: CreateClientConfig = (config) => ({
    ...config,
    baseUrl: env.BACKEND_HOST || "http://127.0.0.1:8000"
});
