import math
from typing import Any

import httpx

from app.config import settings
from app.models import (
    NutritionSizeUnit,
    OpenFoodFactsProductPublic,
    ProductBarcodePreviewPublic,
    ProductNutritionBasis,
    normalize_food_barcode,
)

OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/api/v3.6/product"
REQUESTED_FIELDS = ",".join(
    (
        "code",
        "product_name",
        "generic_name",
        "brands",
        "image_front_url",
        "product_quantity",
        "product_quantity_unit",
        "serving_quantity",
        "serving_quantity_unit",
        "nutrition",
        "nutriments",
    )
)


class ProductNotFoundError(Exception):
    pass


class OpenFoodFactsUnavailableError(Exception):
    pass


class UnsupportedNutritionBasisError(Exception):
    pass


def _upstream_nutrient_names(name: str) -> tuple[str, ...]:
    # Open Food Facts calls this nutrient "proteins" in both its current and legacy
    # payloads. Keep accepting the singular spelling for older/cached payloads.
    return ("proteins", "protein") if name == "protein" else (name,)


def _number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0 else None


def _grams(value: Any, unit: Any) -> float | None:
    amount = _number(value)
    if amount is None:
        return None

    normalized_unit = str(unit or "").strip().lower()
    factors = {
        "kg": 1000,
        "g": 1,
        "mg": 0.001,
        "µg": 0.000001,
        "ug": 0.000001,
    }
    factor = factors.get(normalized_unit)
    if factor is None:
        return None
    result = amount * factor
    return result if math.isfinite(result) else None


def _optional_text(value: Any, max_length: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized[:max_length] or None


def _nested_nutrient(product: dict[str, Any], name: str) -> float | None:
    nutrition = product.get("nutrition")
    if not isinstance(nutrition, dict):
        return None
    aggregated = nutrition.get("aggregated_set", {})
    if not isinstance(aggregated, dict):
        return None
    nutrients = aggregated.get("nutrients", {})
    if not isinstance(nutrients, dict):
        return None
    nutrient: Any = None
    for upstream_name in _upstream_nutrient_names(name):
        candidate = nutrients.get(upstream_name)
        if isinstance(candidate, dict):
            nutrient = candidate
            break
    if not isinstance(nutrient, dict):
        return None

    value = nutrient.get("value")
    if value is None:
        value = nutrient.get("value_computed")
    if name == "energy-kcal":
        return _number(value)
    if name == "energy-kj":
        kilojoules = _number(value)
        return kilojoules / 4.184 if kilojoules is not None else None
    return _grams(value, nutrient.get("unit"))


def _legacy_nutrient(product: dict[str, Any], name: str) -> float | None:
    nutriments = product.get("nutriments", {})
    if not isinstance(nutriments, dict):
        return None
    value = next(
        (
            nutriments[f"{upstream_name}_100g"]
            for upstream_name in _upstream_nutrient_names(name)
            if f"{upstream_name}_100g" in nutriments
        ),
        None,
    )
    if name == "energy-kcal":
        return _number(value)
    return _number(value)


def _nutrient(product: dict[str, Any], name: str) -> float | None:
    nested = _nested_nutrient(product, name)
    return nested if nested is not None else _legacy_nutrient(product, name)


def _weight_per_piece(product: dict[str, Any]) -> int:
    for prefix in ("serving", "product"):
        grams = _grams(
            product.get(f"{prefix}_quantity"),
            product.get(f"{prefix}_quantity_unit"),
        )
        if grams and grams >= 1:
            return round(grams)
    return 1


def _size(
    product: dict[str, Any], prefix: str
) -> tuple[float | None, NutritionSizeUnit | None]:
    amount = _number(product.get(f"{prefix}_quantity"))
    if amount is None or amount <= 0:
        return None, None
    raw_unit = str(product.get(f"{prefix}_quantity_unit") or "").strip().lower()
    if raw_unit in {"g", "gram", "grams"}:
        return amount, NutritionSizeUnit.GRAM
    if raw_unit in {"kg", "kilogram", "kilograms"}:
        converted = amount * 1000
        return (
            (converted, NutritionSizeUnit.GRAM)
            if math.isfinite(converted)
            else (None, None)
        )
    if raw_unit in {"ml", "milliliter", "milliliters", "millilitre"}:
        return amount, NutritionSizeUnit.MILLILITER
    if raw_unit in {"l", "liter", "liters", "litre", "litres"}:
        converted = amount * 1000
        return (
            (converted, NutritionSizeUnit.MILLILITER)
            if math.isfinite(converted)
            else (None, None)
        )
    return None, None


def _reported_nutrition_basis(
    product: dict[str, Any],
) -> ProductNutritionBasis | None:
    nutrition = product.get("nutrition")
    aggregated = (
        nutrition.get("aggregated_set", {}) if isinstance(nutrition, dict) else {}
    )
    if not isinstance(aggregated, dict):
        return None
    raw_basis = str(aggregated.get("per") or "").strip().casefold()
    if not raw_basis:
        return None
    normalized = raw_basis.replace("_", "").replace("-", "").replace(" ", "")
    if normalized in {"100g", "100gram", "100grams"}:
        return ProductNutritionBasis.PER_100G
    if normalized in {"100ml", "100milliliter", "100milliliters"}:
        return ProductNutritionBasis.PER_100ML
    if normalized in {"serving", "portion"}:
        return ProductNutritionBasis.PER_SERVING
    if normalized in {"product", "package", "pack", "unit"}:
        return ProductNutritionBasis.PER_PACKAGE
    raise UnsupportedNutritionBasisError(
        f"Unsupported Open Food Facts nutrition basis: {raw_basis}"
    )


def _draft_nutrition(
    product: dict[str, Any],
) -> tuple[ProductNutritionBasis, dict[str, float | None]]:
    nutrition = product.get("nutrition")
    aggregated = (
        nutrition.get("aggregated_set", {}) if isinstance(nutrition, dict) else {}
    )
    nested_nutrients = (
        aggregated.get("nutrients") if isinstance(aggregated, dict) else None
    )
    names = ("energy-kcal", "carbohydrates", "fat", "protein")
    if isinstance(nested_nutrients, dict):
        basis = _reported_nutrition_basis(product)
        if basis is None:
            raise UnsupportedNutritionBasisError(
                "Open Food Facts did not report a basis for its nutrition values"
            )
        nutrients = {name: _nested_nutrient(product, name) for name in names}
        if nutrients["energy-kcal"] is None:
            nutrients["energy-kcal"] = _nested_nutrient(product, "energy-kj")
        return basis, nutrients

    nutrients = {name: _legacy_nutrient(product, name) for name in names}
    if nutrients["energy-kcal"] is None:
        kilojoules = _legacy_nutrient(product, "energy-kj")
        if kilojoules is not None:
            nutrients["energy-kcal"] = kilojoules / 4.184

    nutriments = product.get("nutriments")
    has_legacy_values = isinstance(nutriments, dict) and any(
        f"{upstream_name}_100g" in nutriments
        for name in (*names, "energy-kj")
        for upstream_name in _upstream_nutrient_names(name)
    )
    if has_legacy_values:
        return ProductNutritionBasis.PER_100G, nutrients

    return _reported_nutrition_basis(
        product
    ) or ProductNutritionBasis.PER_100G, nutrients


def parse_product_draft(
    payload: dict[str, Any], requested_barcode: str
) -> ProductBarcodePreviewPublic:
    """Preserve Open Food Facts' exact basis and unknown nutrient values."""
    product = payload.get("product")
    if not isinstance(product, dict):
        raise ProductNotFoundError

    title = product.get("product_name") or product.get("generic_name")
    if not isinstance(title, str) or not title.strip():
        title = f"Product {product.get('code') or requested_barcode}"

    nutrition_basis, nutrients = _draft_nutrition(product)
    serving_size, serving_unit = _size(product, "serving")
    package_size, package_unit = _size(product, "product")
    field_names = {
        "energy-kcal": "calories",
        "carbohydrates": "carbohydrates",
        "fat": "fat",
        "protein": "protein",
    }
    missing = [field_names[name] for name, value in nutrients.items() if value is None]

    raw_barcode = str(product.get("code") or requested_barcode)
    try:
        barcode = normalize_food_barcode(raw_barcode) or requested_barcode
    except ValueError:
        barcode = requested_barcode

    return ProductBarcodePreviewPublic(
        barcode=barcode,
        title=title.strip()[:255],
        brand=_optional_text(product.get("brands"), 255),
        image_url=_optional_text(product.get("image_front_url"), 1000),
        nutrition_basis=nutrition_basis,
        calories=nutrients["energy-kcal"],
        carbohydrates=nutrients["carbohydrates"],
        fat=nutrients["fat"],
        protein=nutrients["protein"],
        serving_size=serving_size,
        serving_size_unit=serving_unit,
        package_size=package_size,
        package_size_unit=package_unit,
        missing_nutrients=missing,
    )


def parse_product(
    payload: dict[str, Any], requested_barcode: str
) -> OpenFoodFactsProductPublic:
    product = payload.get("product")
    if not isinstance(product, dict):
        raise ProductNotFoundError

    title = product.get("product_name") or product.get("generic_name")
    if not isinstance(title, str) or not title.strip():
        title = f"Product {product.get('code') or requested_barcode}"

    nutrient_names = ("energy-kcal", "carbohydrates", "fat", "protein")
    nutrients = {name: _nutrient(product, name) for name in nutrient_names}
    if nutrients["energy-kcal"] is None:
        nutrients["energy-kcal"] = _nested_nutrient(product, "energy-kj")
    missing = [name for name, value in nutrients.items() if value is None]
    nutrition = product.get("nutrition")
    aggregated = (
        nutrition.get("aggregated_set", {}) if isinstance(nutrition, dict) else {}
    )
    nutrition_basis = (
        aggregated.get("per") if isinstance(aggregated, dict) else None
    ) or "100g"

    return OpenFoodFactsProductPublic(
        barcode=str(product.get("code") or requested_barcode),
        title=title.strip()[:255],
        brand=_optional_text(product.get("brands"), 255),
        image_url=_optional_text(product.get("image_front_url"), 1000),
        calories=round(nutrients["energy-kcal"] or 0),
        carbohydrates=round(nutrients["carbohydrates"] or 0, 2),
        fat=round(nutrients["fat"] or 0, 2),
        protein=round(nutrients["protein"] or 0, 2),
        weight_per_piece=max(_weight_per_piece(product), 1),
        nutrition_basis=str(nutrition_basis),
        missing_nutrients=missing,
    )


def _lookup_payload(barcode: str, client: httpx.Client | None = None) -> dict[str, Any]:
    owns_client = client is None
    if client is None:
        client = httpx.Client(timeout=8, follow_redirects=True)

    try:
        response = client.get(
            f"{OPENFOODFACTS_API_URL}/{barcode}",
            params={"fields": REQUESTED_FIELDS, "lc": "en"},
            headers={
                "User-Agent": settings.OPENFOODFACTS_USER_AGENT
                or f"{settings.PROJECT_NAME}/1.0 ({settings.FRONTEND_HOST})"
            },
        )
    except httpx.HTTPError as exc:
        raise OpenFoodFactsUnavailableError from exc
    finally:
        if owns_client:
            client.close()

    if response.status_code == 404:
        raise ProductNotFoundError
    if response.status_code >= 400:
        raise OpenFoodFactsUnavailableError

    try:
        payload = response.json()
    except ValueError as exc:
        raise OpenFoodFactsUnavailableError from exc

    if not isinstance(payload, dict):
        raise OpenFoodFactsUnavailableError

    return payload


def lookup_product(
    barcode: str, client: httpx.Client | None = None
) -> OpenFoodFactsProductPublic:
    return parse_product(_lookup_payload(barcode, client), barcode)


def lookup_product_draft(
    barcode: str, client: httpx.Client | None = None
) -> ProductBarcodePreviewPublic:
    return parse_product_draft(_lookup_payload(barcode, client), barcode)
