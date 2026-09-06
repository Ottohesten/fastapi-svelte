export type CameraZoomCapabilities = {
    min: number;
    max: number;
    step?: number;
};

export type CameraZoomConfiguration = Omit<CameraZoomCapabilities, "step"> & {
    step: number;
    value: number;
};

const WIDE_BARCODE_ZOOM = 1;

function clamp(value: number, min: number, max: number) {
    return Math.min(Math.max(value, min), max);
}

export function getCameraZoomConfiguration(
    capabilities: CameraZoomCapabilities | undefined
): CameraZoomConfiguration | null {
    if (
        !capabilities ||
        !Number.isFinite(capabilities.min) ||
        !Number.isFinite(capabilities.max) ||
        capabilities.max <= capabilities.min
    ) {
        return null;
    }

    const step =
        capabilities.step && Number.isFinite(capabilities.step) && capabilities.step > 0
            ? capabilities.step
            : Math.max((capabilities.max - capabilities.min) / 100, 0.1);
    return {
        min: capabilities.min,
        max: capabilities.max,
        step,
        value: clamp(WIDE_BARCODE_ZOOM, capabilities.min, capabilities.max)
    };
}

export function clampCameraZoom(value: number, configuration: CameraZoomConfiguration) {
    return clamp(value, configuration.min, configuration.max);
}
