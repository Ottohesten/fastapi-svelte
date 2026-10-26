import * as env from "$app/env/public";
import * as Sentry from "@sentry/sveltekit";
import {
    hasBrowserTelemetryOptOut,
    parseTracesSampleRate,
    privacyFirstDataCollection
} from "#lib/observability/sentry-config.js";

const dsn = env.PUBLIC_SENTRY_DSN;

Sentry.init({
    dsn,
    enabled: Boolean(dsn) && !hasBrowserTelemetryOptOut(navigator),
    environment: env.PUBLIC_SENTRY_ENVIRONMENT || "local",
    tracesSampleRate: parseTracesSampleRate(env.PUBLIC_SENTRY_TRACES_SAMPLE_RATE),
    dataCollection: privacyFirstDataCollection()
});

export const handleError = Sentry.handleErrorWithSentry();
