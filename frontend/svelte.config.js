// import adapter from '@sveltejs/adapter-auto';
import adapter from "@sveltejs/adapter-node";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
    // Consult https://svelte.dev/docs/kit/integrations
    // for more information about preprocessors
    preprocess: vitePreprocess(),

    kit: {
        // adapter-auto only supports some environments, see https://svelte.dev/docs/kit/adapter-auto for a list.
        // If your environment is not supported, or you settled on a specific environment, switch out the adapter.
        // See https://svelte.dev/docs/kit/adapters for more information about adapters.
        adapter: adapter(),
        csrf: {
            trustedOrigins: [
                "https://internationaleregler.dk",
                "https://fastapi-svelte-backend.onrender.com",
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ]
        }
    }
};

export default config;
