import * as privateEnv from "$app/env/private";
import * as publicEnv from "$app/env/public";
import * as Sentry from "@sentry/sveltekit";
import {
    parseTracesSampleRate,
    privacyFirstDataCollection
} from "#lib/observability/sentry-config.js";

const dsn = publicEnv.PUBLIC_SENTRY_DSN || privateEnv.SENTRY_DSN;

Sentry.init({
    dsn,
    enabled: Boolean(dsn),
    environment: publicEnv.PUBLIC_SENTRY_ENVIRONMENT || privateEnv.ENVIRONMENT || "local",
    tracesSampleRate: parseTracesSampleRate(
        privateEnv.SENTRY_TRACES_SAMPLE_RATE || publicEnv.PUBLIC_SENTRY_TRACES_SAMPLE_RATE
    ),
    dataCollection: privacyFirstDataCollection()
});
