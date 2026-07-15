import { env } from "$env/dynamic/public";
import * as Sentry from "@sentry/sveltekit";
import {
    hasBrowserTelemetryOptOut,
    parseTracesSampleRate,
    privacyFirstDataCollection
} from "$lib/observability/sentry-config";

const dsn = env.PUBLIC_SENTRY_DSN;

Sentry.init({
    dsn,
    enabled: Boolean(dsn) && !hasBrowserTelemetryOptOut(navigator),
    environment: env.PUBLIC_SENTRY_ENVIRONMENT || "local",
    tracesSampleRate: parseTracesSampleRate(env.PUBLIC_SENTRY_TRACES_SAMPLE_RATE),
    enableMetrics: false,
    dataCollection: privacyFirstDataCollection()
});

export const handleError = Sentry.handleErrorWithSentry();
