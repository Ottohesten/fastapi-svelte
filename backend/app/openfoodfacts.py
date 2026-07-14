from typing import Any

import httpx

from app.config import settings
from app.models import OpenFoodFactsProductPublic


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


def _number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _grams(value: Any, unit: Any) -> float | None:
    amount = _number(value)
    if amount is None:
        return None

    normalized_unit = str(unit or "g").strip().lower()
    factors = {
        "kg": 1000,
        "g": 1,
        "mg": 0.001,
        "µg": 0.000001,
        "ug": 0.000001,
    }
    factor = factors.get(normalized_unit)
    return amount * factor if factor is not None else None


def _nested_nutrient(product: dict[str, Any], name: str) -> float | None:
    nutrition = product.get("nutrition")
    if not isinstance(nutrition, dict):
        return None
    aggregated = nutrition.get("aggregated_set", {})
    if not isinstance(aggregated, dict):
        return None
    nutrient = aggregated.get("nutrients", {}).get(name, {})
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
    value = nutriments.get(f"{name}_100g")
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
    nutrition_basis = aggregated.get("per") or "100g"

    return OpenFoodFactsProductPublic(
        barcode=str(product.get("code") or requested_barcode),
        title=title.strip()[:255],
        brand=(str(product["brands"]).strip() or None)
        if product.get("brands")
        else None,
        image_url=product.get("image_front_url"),
        calories=round(nutrients["energy-kcal"] or 0),
        carbohydrates=round(nutrients["carbohydrates"] or 0, 2),
        fat=round(nutrients["fat"] or 0, 2),
        protein=round(nutrients["protein"] or 0, 2),
        weight_per_piece=max(_weight_per_piece(product), 1),
        nutrition_basis=str(nutrition_basis),
        missing_nutrients=missing,
    )


def lookup_product(
    barcode: str, client: httpx.Client | None = None
) -> OpenFoodFactsProductPublic:
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

    return parse_product(payload, barcode)
