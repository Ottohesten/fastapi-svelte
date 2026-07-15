import { sveltekit } from "@sveltejs/kit/vite";
import { sentrySvelteKit } from "@sentry/sveltekit";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(async ({ mode }) => {
    const buildEnvironment = loadEnv(mode, rootDir, "");
    const hasSourceMapCredentials = Boolean(
        buildEnvironment.SENTRY_AUTH_TOKEN &&
        buildEnvironment.SENTRY_ORG &&
        buildEnvironment.SENTRY_PROJECT
    );

    return {
        plugins: [
            ...(await sentrySvelteKit({
                autoUploadSourceMaps: hasSourceMapCredentials,
                authToken: buildEnvironment.SENTRY_AUTH_TOKEN,
                org: buildEnvironment.SENTRY_ORG,
                project: buildEnvironment.SENTRY_PROJECT
            })),
            sveltekit(),
            tailwindcss()
        ],
        // resolve: {
        //     alias: {
        //         // formsnap's package.json only provides a "svelte" export condition
        //         // which some resolvers don't honor. Point the bare import to the
        //         // built svelte entry so Vite can resolve it reliably on all hosts.
        //         formsnap: path.resolve(rootDir, "node_modules", "formsnap", "dist", "index.js")
        //     }
        // },
        server: {
            fs: {
                // Allow Bun hoisted deps from repo root (e.g. ../node_modules/.bun/@sveltejs+kit...)
                allow: [path.resolve(rootDir, "..", "node_modules")]
            }
        }
    };
});
