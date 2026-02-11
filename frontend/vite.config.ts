import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    plugins: [sveltekit(), tailwindcss()],
    server: {
        fs: {
            // Allow Bun hoisted deps from repo root (e.g. ../node_modules/.bun/@sveltejs+kit...)
            allow: [path.resolve(rootDir, "..", "node_modules")]
        }
    }
});
