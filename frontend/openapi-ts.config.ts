import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
    input: "./openapi.json", // sign up at app.heyapi.dev
    output: "./src/lib/client",
    // output: "./src/client",
    plugins: [
        {
            name: "@hey-api/client-fetch",
            runtimeConfigPath: "$lib/hey-api"
        },
        {
            dates: true,
            name: "@hey-api/transformers"
        },
        {
            name: "@hey-api/schemas",
            type: "json"
        },
        {
            auth: true,
            name: "@hey-api/sdk",
            transformer: true,
            operations: {
                containerName: { name: "{{name}}Service" },
                methodName: { name: "{{name}}", casing: "PascalCase" },
                nesting(operation) {
                    const operationId = String(operation.operationId ?? operation.id ?? "");
                    const tags = (operation.tags ?? []).map((tag) => String(tag).toLowerCase());
                    const operationIdLower = operationId.toLowerCase();

                    // FastAPI operationIds here are tag-prefixed, e.g. "users-read_users".
                    // When grouping by tags we remove any tag prefix to avoid methods like "UsersReadUsers".
                    for (const tag of tags) {
                        const candidates = [tag + "-", tag + "_", tag + "."];
                        for (const prefix of candidates) {
                            if (operationIdLower.startsWith(prefix)) {
                                return [operationId.slice(prefix.length)];
                            }
                        }
                    }

                    return [operationId];
                },
                strategy: "byTags"
            }
        }
    ]
});
