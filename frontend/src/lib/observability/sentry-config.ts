const DEFAULT_TRACES_SAMPLE_RATE = 0.1;

export function parseTracesSampleRate(value: string | undefined): number {
    if (!value) return DEFAULT_TRACES_SAMPLE_RATE;

    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= 0 && parsed <= 1
        ? parsed
        : DEFAULT_TRACES_SAMPLE_RATE;
}

export function hasBrowserTelemetryOptOut(navigatorValue: Navigator): boolean {
    const navigatorWithGlobalPrivacyControl = navigatorValue as Navigator & {
        globalPrivacyControl?: boolean;
    };

    return (
        navigatorValue.doNotTrack === "1" ||
        navigatorValue.doNotTrack === "yes" ||
        navigatorWithGlobalPrivacyControl.globalPrivacyControl === true
    );
}

export function privacyFirstDataCollection() {
    return {
        userInfo: false,
        cookies: false,
        httpHeaders: {
            request: false,
            response: false
        },
        httpBodies: [],
        queryParams: false,
        genAI: {
            inputs: false,
            outputs: false
        },
        stackFrameVariables: false,
        frameContextLines: 5
    };
}
