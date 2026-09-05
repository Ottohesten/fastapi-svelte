import type {
    EntryUnit,
    NutritionEntryDraft,
    NutritionIngredientOption,
    NutritionProduct,
    NutritionRecipeOption,
    NutritionValues
} from "$lib/nutrition/types";

export function validProductUnits(product: NutritionProduct): EntryUnit[] {
    const units: EntryUnit[] = [];
    const add = (unit: EntryUnit) => {
        if (!units.includes(unit)) units.push(unit);
    };

    const nutritionBasis = product.nutrition_basis ?? "per_100g";
    if (nutritionBasis === "per_100g") add("g");
    if (nutritionBasis === "per_100ml") add("ml");
    if (nutritionBasis === "per_serving") add("serving");
    if (nutritionBasis === "per_package") add("package");

    const basisUnit =
        nutritionBasis === "per_100g"
            ? "g"
            : nutritionBasis === "per_100ml"
              ? "ml"
              : nutritionBasis === "per_serving"
                ? product.serving_size_unit
                : product.package_size_unit;

    if (basisUnit) add(basisUnit);
    if (basisUnit && product.serving_size != null && product.serving_size_unit === basisUnit) {
        add("serving");
    }
    if (basisUnit && product.package_size != null && product.package_size_unit === basisUnit) {
        add("package");
    }
    return units;
}

export function roundNutrition(value: number): number {
    return Math.round((Number.isFinite(value) ? value : 0) * 10) / 10;
}

export function formatNutrition(value: number | null | undefined): string {
    if (value == null) return "Unknown";
    return roundNutrition(value).toLocaleString("en-DK", { maximumFractionDigits: 1 });
}

export function defaultMealType(now = new Date()) {
    const hour = now.getHours();
    if (hour < 11) return "breakfast" as const;
    if (hour < 15) return "lunch" as const;
    if (hour < 21) return "dinner" as const;
    return "snack" as const;
}

export function draftPreview(draft: NutritionEntryDraft): NutritionValues | null {
    if (draft.source_type === "manual") {
        if (draft.calories === null || !Number.isFinite(draft.calories)) return null;
        return {
            calories: draft.calories,
            carbohydrates: draft.carbohydrates,
            fat: draft.fat,
            protein: draft.protein
        };
    }
    return draft.preview;
}

export function draftIsComplete(
    draft: NutritionEntryDraft,
    recipes: NutritionRecipeOption[],
    products: NutritionProduct[],
    ingredients: NutritionIngredientOption[]
): boolean {
    if (draft.status !== "resolved") return false;
    if (!Number.isFinite(draft.quantity) || draft.quantity <= 0) return false;
    if (draft.source_type === "recipe") {
        return draft.unit === "serving" && recipes.some((recipe) => recipe.id === draft.source_id);
    }
    if (draft.source_type === "product") {
        const product = products.find((item) => item.id === draft.source_id);
        return product !== undefined && validProductUnits(product).includes(draft.unit);
    }
    if (draft.source_type === "ingredient") {
        const ingredient = ingredients.find((item) => item.id === draft.source_id);
        return (
            ingredient !== undefined &&
            (draft.unit === "g" ||
                (draft.unit === "piece" &&
                    ingredient.weight_per_piece !== null &&
                    ingredient.weight_per_piece > 0))
        );
    }
    return (
        draft.quantity === 1 &&
        draft.unit === "piece" &&
        draft.title.trim().length > 0 &&
        draft.calories !== null &&
        Number.isFinite(draft.calories) &&
        draft.calories >= 0
    );
}
