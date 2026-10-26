import { defineEnvVars } from "@sveltejs/kit/env";

const optional = (value: string | undefined) => value ?? "";

export const variables = defineEnvVars({
    BACKEND_HOST: { schema: (value: string | undefined) => value || "http://127.0.0.1:8000" },
    ANALYTICS_INGEST_TOKEN: { schema: optional },
    ENVIRONMENT: { schema: optional },
    SENTRY_DSN: { schema: optional },
    SENTRY_TRACES_SAMPLE_RATE: { schema: optional },
    PUBLIC_SENTRY_DSN: { schema: optional, public: true },
    PUBLIC_SENTRY_ENVIRONMENT: { schema: optional, public: true },
    PUBLIC_SENTRY_TRACES_SAMPLE_RATE: { schema: optional, public: true }
});
