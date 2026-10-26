import { describe, expect, test } from "bun:test";
import {
    NutritionBatchFormSchema,
    NutritionEntryFormSchema,
    ProductFormSchema,
    QuickAddFormSchema,
    emptyProductForm,
    type NutritionEntryForm
} from "./nutrition";

const sourceId = "11111111-1111-4111-8111-111111111111";

function entry(overrides: Partial<NutritionEntryForm> = {}): NutritionEntryForm {
    return {
        id: "",
        client_id: "test-entry",
        original_text: "",
        log_date: "2026-09-04",
        meal_type: "lunch",
        source_type: "recipe",
        source_id: sourceId,
        title: "",
        brand: "",
        note: "",
        quantity: 1,
        unit: "serving",
        calories: null,
        carbohydrates: null,
        fat: null,
        protein: null,
        status: "resolved",
        candidates: [],
        preview: null,
        row_message: null,
        ...overrides
    };
}

describe("nutrition form schemas", () => {
    test("preserves unknown product macros but requires calories", () => {
        const missingCalories = ProductFormSchema.safeParse({
            ...emptyProductForm(),
            title: "Frozen pizza"
        });
        expect(missingCalories.success).toBe(false);

        const valid = ProductFormSchema.safeParse({
            ...emptyProductForm(),
            title: " Frozen pizza ",
            calories: 720,
            fat: null
        });
        expect(valid.success).toBe(true);
        if (valid.success) {
            expect(valid.data.title).toBe("Frozen pizza");
            expect(valid.data.fat).toBeNull();
        }
    });

    test("rejects malformed product identifiers, barcodes, and sizes", () => {
        expect(
            ProductFormSchema.safeParse({
                ...emptyProductForm(),
                id: "not-a-uuid",
                title: "Pizza",
                calories: 1
            }).success
        ).toBe(false);
        expect(
            ProductFormSchema.safeParse({
                ...emptyProductForm(),
                title: "Pizza",
                calories: 1,
                barcode: "12ab"
            }).success
        ).toBe(false);
        expect(
            ProductFormSchema.safeParse({
                ...emptyProductForm(),
                title: "Pizza",
                calories: 1,
                package_size: 0
            }).success
        ).toBe(false);
    });

    test("validates sourced and manual diary entries by source type", () => {
        expect(NutritionEntryFormSchema.safeParse(entry({ source_id: "" })).success).toBe(false);
        expect(
            NutritionEntryFormSchema.safeParse(
                entry({
                    source_type: "manual",
                    source_id: "",
                    title: "Birthday cake",
                    unit: "piece",
                    calories: 320
                })
            ).success
        ).toBe(true);
        expect(
            NutritionEntryFormSchema.safeParse(
                entry({
                    source_type: "manual",
                    source_id: "",
                    title: "Birthday cake",
                    unit: "piece",
                    calories: null
                })
            ).success
        ).toBe(false);
    });

    test("rejects missing quantities and oversized batches", () => {
        expect(NutritionEntryFormSchema.safeParse(entry({ quantity: 0 })).success).toBe(false);
        expect(
            NutritionBatchFormSchema.safeParse({
                entries: Array.from({ length: 51 }, (_, index) =>
                    entry({ client_id: `entry-${index}` })
                )
            }).success
        ).toBe(false);
    });

    test("trims quick-add text and validates its local date", () => {
        const parsed = QuickAddFormSchema.safeParse({
            text: "  Morgenmad:\n1 portion oatmeal  ",
            log_date: "2026-09-04",
            default_meal: "breakfast"
        });
        expect(parsed.success).toBe(true);
        if (parsed.success) expect(parsed.data.text).toBe("Morgenmad:\n1 portion oatmeal");

        expect(
            QuickAddFormSchema.safeParse({
                text: "oatmeal",
                log_date: "04-09-2026",
                default_meal: "breakfast"
            }).success
        ).toBe(false);
    });
});
