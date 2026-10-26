import { z } from "zod";

const optionalText = (maximum: number) => z.string().trim().max(maximum).default("");

const optionalNutritionValue = z
    .number()
    .finite("Enter a finite number")
    .nonnegative("Enter zero or a positive number")
    .nullable()
    .default(null);

const optionalSize = z
    .number()
    .finite("Enter a finite number")
    .positive("Enter a number greater than zero")
    .nullable()
    .default(null);

export const ProductFormSchema = z
    .object({
        id: z.string().uuid().or(z.literal("")).default(""),
        title: z
            .string()
            .trim()
            .min(1, "Product name is required")
            .max(255, "Product name must be 255 characters or fewer"),
        brand: optionalText(255),
        barcode: z
            .string()
            .trim()
            .max(24, "Barcode must be 24 digits or fewer")
            .refine((value) => value === "" || /^\d{4,24}$/.test(value), {
                message: "Barcode must contain between 4 and 24 digits"
            })
            .default(""),
        image_url: optionalText(1000),
        nutrition_basis: z
            .enum(["per_100g", "per_100ml", "per_serving", "per_package"])
            .default("per_100g"),
        calories: optionalNutritionValue,
        carbohydrates: optionalNutritionValue,
        fat: optionalNutritionValue,
        protein: optionalNutritionValue,
        serving_size: optionalSize,
        serving_size_unit: z.enum(["g", "ml"]).default("g"),
        package_size: optionalSize,
        package_size_unit: z.enum(["g", "ml"]).default("g")
    })
    .superRefine((product, context) => {
        if (product.calories === null) {
            context.addIssue({
                code: "custom",
                message: "Calories are required",
                path: ["calories"]
            });
        }
    });

export type ProductFormData = z.infer<typeof ProductFormSchema>;

export function emptyProductForm(): ProductFormData {
    return {
        id: "",
        title: "",
        brand: "",
        barcode: "",
        image_url: "",
        nutrition_basis: "per_100g",
        calories: null,
        carbohydrates: null,
        fat: null,
        protein: null,
        serving_size: null,
        serving_size_unit: "g",
        package_size: null,
        package_size_unit: "g"
    };
}

export const nutritionMealTypes = ["breakfast", "lunch", "dinner", "snack"] as const;
export const nutritionSourceTypes = ["recipe", "product", "ingredient", "manual"] as const;
export const nutritionEntryUnits = ["serving", "g", "ml", "piece", "package"] as const;

const isoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Choose a valid date");

const candidateSchema = z.object({
    source_type: z.enum(["recipe", "product", "ingredient"]),
    source_id: z.string().uuid(),
    title: z.string(),
    similarity: z.number().nullable().optional()
});

const nutritionPreviewSchema = z.object({
    calories: z.number().finite().nonnegative(),
    carbohydrates: z.number().finite().nonnegative().nullable(),
    fat: z.number().finite().nonnegative().nullable(),
    protein: z.number().finite().nonnegative().nullable()
});

/** Form model shared by the single-entry and quick-add batch editors. */
export const NutritionEntryFormSchema = z
    .object({
        id: z.string().uuid().or(z.literal("")).default(""),
        client_id: z.string().min(1),
        original_text: z.string().default(""),
        log_date: isoDate,
        meal_type: z.enum(nutritionMealTypes),
        source_type: z.enum(nutritionSourceTypes),
        source_id: z.string().uuid().or(z.literal("")).default(""),
        title: z.string().trim().max(255).default(""),
        brand: z.string().trim().max(255).default(""),
        note: z.string().trim().max(500).default(""),
        quantity: z.number().finite().positive("Amount must be greater than zero"),
        unit: z.enum(nutritionEntryUnits),
        calories: optionalNutritionValue,
        carbohydrates: optionalNutritionValue,
        fat: optionalNutritionValue,
        protein: optionalNutritionValue,
        status: z
            .enum([
                "resolved",
                "ambiguous",
                "needs_quantity",
                "needs_nutrition",
                "invalid",
                "unmatched"
            ])
            .default("resolved"),
        candidates: z.array(candidateSchema).default([]),
        preview: nutritionPreviewSchema.nullable().default(null),
        row_message: z.string().nullable().default(null)
    })
    .superRefine((entry, context) => {
        if (entry.source_type === "manual") {
            if (!entry.title) {
                context.addIssue({
                    code: "custom",
                    path: ["title"],
                    message: "Description is required"
                });
            }
            if (entry.calories === null) {
                context.addIssue({
                    code: "custom",
                    path: ["calories"],
                    message: "Calories are required"
                });
            }
            if (entry.quantity !== 1 || entry.unit !== "piece") {
                context.addIssue({
                    code: "custom",
                    path: ["quantity"],
                    message: "Manual nutrition must describe one complete entry"
                });
            }
        } else if (!entry.source_id) {
            context.addIssue({
                code: "custom",
                path: ["source_id"],
                message: "Choose a saved food"
            });
        }
    });

export const NutritionBatchFormSchema = z.object({
    entries: z
        .array(NutritionEntryFormSchema)
        .min(1, "Review at least one entry")
        .max(50, "A batch can contain at most 50 entries")
});

export const QuickAddFormSchema = z.object({
    text: z.string().trim().min(1, "Enter at least one food").max(4000),
    log_date: isoDate,
    default_meal: z.enum(nutritionMealTypes)
});

export const NutritionMoveFormSchema = z.object({
    id: z.string().uuid(),
    log_date: isoDate,
    meal_type: z.enum(nutritionMealTypes),
    note: z.string().trim().max(500).default("")
});

export const NutritionDeleteFormSchema = z.object({
    id: z.string().uuid()
});

export const ProductDeleteFormSchema = NutritionDeleteFormSchema;

export type NutritionEntryForm = z.infer<typeof NutritionEntryFormSchema>;
