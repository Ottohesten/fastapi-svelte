import { env as privateEnv } from "$env/dynamic/private";
import { env as publicEnv } from "$env/dynamic/public";
import * as Sentry from "@sentry/sveltekit";
import {
    parseTracesSampleRate,
    privacyFirstDataCollection
} from "$lib/observability/sentry-config";

const dsn = publicEnv.PUBLIC_SENTRY_DSN || privateEnv.SENTRY_DSN;

Sentry.init({
    dsn,
    enabled: Boolean(dsn),
    environment: publicEnv.PUBLIC_SENTRY_ENVIRONMENT || privateEnv.ENVIRONMENT || "local",
    tracesSampleRate: parseTracesSampleRate(
        privateEnv.SENTRY_TRACES_SAMPLE_RATE || publicEnv.PUBLIC_SENTRY_TRACES_SAMPLE_RATE
    ),
    enableMetrics: false,
    dataCollection: privacyFirstDataCollection()
});
