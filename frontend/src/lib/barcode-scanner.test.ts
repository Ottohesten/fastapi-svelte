import { describe, expect, test } from "bun:test";
import { clampCameraZoom, getCameraZoomConfiguration } from "$lib/barcode-scanner";

describe("barcode scanner camera zoom", () => {
    test("starts with a wide 1x field of view", () => {
        expect(getCameraZoomConfiguration({ min: 1, max: 8, step: 0.1 })).toEqual({
            min: 1,
            max: 8,
            step: 0.1,
            value: 1
        });
    });

    test("starts at 1x instead of retaining a camera's higher current zoom", () => {
        expect(getCameraZoomConfiguration({ min: 1, max: 4 })).toEqual({
            min: 1,
            max: 4,
            step: 0.1,
            value: 1
        });
        expect(getCameraZoomConfiguration({ min: 2, max: 4 })).toMatchObject({
            value: 2
        });
    });

    test("ignores unavailable zoom and clamps user changes", () => {
        expect(getCameraZoomConfiguration(undefined)).toBeNull();
        expect(getCameraZoomConfiguration({ min: 1, max: 1 })).toBeNull();

        const configuration = getCameraZoomConfiguration({ min: 1, max: 3 })!;
        expect(clampCameraZoom(0, configuration)).toBe(1);
        expect(clampCameraZoom(5, configuration)).toBe(3);
    });
});
