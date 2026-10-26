import type {
    NutritionCatalogIngredientPublic,
    NutritionCatalogPublic,
    NutritionCatalogRecipePublic,
    NutritionDayPublic,
    NutritionEntryPublic,
    NutritionEntryUnit,
    NutritionMealType,
    NutritionSizeUnit,
    NutritionSourceType,
    NutritionTotalsPublic,
    ProductBarcodePreviewPublic,
    ProductNutritionBasis,
    ProductPublic,
    QuickAddCandidatePublic
} from "$lib/client";
import type { NutritionEntryForm } from "$lib/schemas/nutrition";

export const mealTypes = [
    "breakfast",
    "lunch",
    "dinner",
    "snack"
] as const satisfies readonly NutritionMealType[];
export type MealType = NutritionMealType;

export const entrySourceTypes = [
    "recipe",
    "product",
    "ingredient",
    "manual"
] as const satisfies readonly NutritionSourceType[];
export type EntrySourceType = NutritionSourceType;

export const entryUnits = [
    "serving",
    "g",
    "ml",
    "piece",
    "package"
] as const satisfies readonly NutritionEntryUnit[];
export type EntryUnit = NutritionEntryUnit;

export const nutritionBases = [
    "per_100g",
    "per_100ml",
    "per_serving",
    "per_package"
] as const satisfies readonly ProductNutritionBasis[];
export type NutritionBasis = ProductNutritionBasis;
export type SizeUnit = NutritionSizeUnit;

export type NutritionValues = {
    calories: number;
    carbohydrates: number | null;
    fat: number | null;
    protein: number | null;
};

// API models are aliases of the generated OpenAPI contract. Only drafts remain UI-owned.
export type NutritionTotals = NutritionTotalsPublic;
export type NutritionRecipeOption = NutritionCatalogRecipePublic;
export type NutritionIngredientOption = NutritionCatalogIngredientPublic;
export type NutritionProduct = ProductPublic;
export type NutritionEntry = NutritionEntryPublic;
export type NutritionDay = NutritionDayPublic;
export type NutritionCatalog = NutritionCatalogPublic;
export type BarcodeProductPreview = ProductBarcodePreviewPublic;
export type QuickAddCandidate = QuickAddCandidatePublic;
export type NutritionEntryDraft = NutritionEntryForm;

export const emptyNutritionValues = (): NutritionValues => ({
    calories: 0,
    carbohydrates: null,
    fat: null,
    protein: null
});

export const emptyNutritionTotals = (): Required<NutritionTotalsPublic> => ({
    calories: 0,
    carbohydrates: 0,
    fat: 0,
    protein: 0,
    carbohydrates_unknown: false,
    fat_unknown: false,
    protein_unknown: false,
    incomplete_entry_count: 0,
    missing_nutrients: []
});

export const mealTypeLabels: Record<MealType, string> = {
    breakfast: "Breakfast",
    lunch: "Lunch",
    dinner: "Dinner",
    snack: "Snack"
};

export const sourceTypeLabels: Record<EntrySourceType, string> = {
    recipe: "Recipe",
    product: "Product",
    ingredient: "Ingredient",
    manual: "Manual"
};

export const nutritionBasisLabels: Record<NutritionBasis, string> = {
    per_100g: "per 100 g",
    per_100ml: "per 100 ml",
    per_serving: "per serving",
    per_package: "per package"
};
