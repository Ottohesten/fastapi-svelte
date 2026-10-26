# Frontend

This application uses SvelteKit 3, Svelte 5, and Bun. SvelteKit configuration lives in
`vite.config.ts`, and application environment variables are declared in `src/env.ts`.
TypeScript stays on version 6 because SvelteKit and svelte-check require its compiler API.

## Developing

Once you've created a project and installed dependencies with `bun install`, start a development server:

```bash
bun run dev

# or start the server and open the app in a new browser tab
bun run dev -- --open
```

## Building

To create a production version of your app:

```bash
bun run build
```

You can preview the production build with `bun run preview`.

The production build uses `@sveltejs/adapter-node`. Start it with `node build/index.js`
(Node 22.17 or newer), or `bun build/index.js`.

If the public origin cannot be derived reliably from request headers, set `ORIGIN` when
**building**, for example `ORIGIN=https://example.com bun run build`. The Vite configuration
passes it to SvelteKit's `paths.origin`; setting `ORIGIN` only when starting the server no
longer works in SvelteKit 3. Alternatively, configure the adapter's `PROTOCOL_HEADER` and
`HOST_HEADER` for a trusted reverse proxy.

Shared-code imports use the `#lib` subpath mappings in `package.json`, with explicit file
extensions (for example `#lib/utils.js` or `#lib/components/RecipeForm.svelte`). The API client
and shadcn configurations use the same mappings.
