import { describe, expect, test } from "bun:test";
import { clampCameraZoom, getCameraZoomConfiguration } from "$lib/barcode-scanner";

describe("barcode scanner camera zoom", () => {
    test("starts with a modest zoom when the camera supports it", () => {
        expect(getCameraZoomConfiguration({ min: 1, max: 8, step: 0.1 }, 1)).toEqual({
            min: 1,
            max: 8,
            step: 0.1,
            value: 1.5
        });
    });

    test("preserves a camera's higher current zoom and respects its range", () => {
        expect(getCameraZoomConfiguration({ min: 1, max: 4 }, 2)).toEqual({
            min: 1,
            max: 4,
            step: 0.1,
            value: 2
        });
        expect(getCameraZoomConfiguration({ min: 1, max: 1.25 }, 1)).toMatchObject({
            value: 1.25
        });
    });

    test("ignores unavailable zoom and clamps user changes", () => {
        expect(getCameraZoomConfiguration(undefined, undefined)).toBeNull();
        expect(getCameraZoomConfiguration({ min: 1, max: 1 }, 1)).toBeNull();

        const configuration = getCameraZoomConfiguration({ min: 1, max: 3 }, 1)!;
        expect(clampCameraZoom(0, configuration)).toBe(1);
        expect(clampCameraZoom(5, configuration)).toBe(3);
    });
});
