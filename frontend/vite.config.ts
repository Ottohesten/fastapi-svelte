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
        resolve: {
            // ProseMirror objects rely on module identity. A second copy in a production chunk
            // makes otherwise valid nodes fail with "Can not convert ... to a Fragment", so
            // always resolve Tiptap's complete ProseMirror graph from this project root.
            dedupe: [
                "@tiptap/core",
                "@tiptap/pm",
                "prosemirror-changeset",
                "prosemirror-commands",
                "prosemirror-dropcursor",
                "prosemirror-gapcursor",
                "prosemirror-history",
                "prosemirror-inputrules",
                "prosemirror-keymap",
                "prosemirror-model",
                "prosemirror-schema-list",
                "prosemirror-state",
                "prosemirror-tables",
                "prosemirror-transform",
                "prosemirror-view"
            ]
        },
        server: {
            fs: {
                // Allow Bun hoisted deps from repo root (e.g. ../node_modules/.bun/@sveltejs+kit...)
                allow: [path.resolve(rootDir, "..", "node_modules")]
            }
        }
    };
});
