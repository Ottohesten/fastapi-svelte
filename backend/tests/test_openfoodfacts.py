import httpx
import pytest

from app.openfoodfacts import (
    OpenFoodFactsUnavailableError,
    ProductNotFoundError,
    lookup_product,
    parse_product,
)


pytestmark = pytest.mark.no_db


def test_parse_v36_product() -> None:
    product = parse_product(
        {
            "product": {
                "code": "03017620422003",
                "product_name": "Hazelnut spread",
                "brands": "Example",
                "product_quantity": 400,
                "product_quantity_unit": "g",
                "nutrition": {
                    "aggregated_set": {
                        "per": "100g",
                        "nutrients": {
                            "energy-kcal": {"value": 539, "unit": "kcal"},
                            "carbohydrates": {"value": 57.5, "unit": "g"},
                            "fat": {"value": 30.9, "unit": "g"},
                            "protein": {"value": 6.3, "unit": "g"},
                        },
                    }
                },
            }
        },
        "03017620422003",
    )

    assert product.title == "Hazelnut spread"
    assert product.calories == 539
    assert product.carbohydrates == 57.5
    assert product.fat == 30.9
    assert product.protein == 6.3
    assert product.weight_per_piece == 400
    assert product.missing_nutrients == []


def test_parse_product_marks_missing_nutrients() -> None:
    product = parse_product(
        {"product": {"code": "12345678", "product_name": "Mystery food"}},
        "12345678",
    )

    assert product.calories == 0
    assert product.missing_nutrients == [
        "energy-kcal",
        "carbohydrates",
        "fat",
        "protein",
    ]


def test_parse_legacy_product_uses_generic_name_and_serving_weight() -> None:
    product = parse_product(
        {
            "product": {
                "generic_name": "Wholegrain crackers",
                "serving_quantity": "0.25",
                "serving_quantity_unit": "kg",
                "nutriments": {
                    "energy-kcal_100g": "420",
                    "carbohydrates_100g": "64.5",
                    "fat_100g": "12.25",
                    "protein_100g": "8",
                },
            }
        },
        "12345678",
    )

    assert product.barcode == "12345678"
    assert product.title == "Wholegrain crackers"
    assert product.calories == 420
    assert product.carbohydrates == 64.5
    assert product.fat == 12.25
    assert product.protein == 8
    assert product.weight_per_piece == 250
    assert product.nutrition_basis == "100g"
    assert product.missing_nutrients == []


def test_parse_product_converts_kilojoules_and_nutrient_units() -> None:
    product = parse_product(
        {
            "product": {
                "code": "12345678",
                "product_name": "Converted food",
                "nutrition": {
                    "aggregated_set": {
                        "per": "serving",
                        "nutrients": {
                            "energy-kj": {"value": 418.4, "unit": "kJ"},
                            "carbohydrates": {"value": 1000, "unit": "mg"},
                            "fat": {"value": 1_000_000, "unit": "µg"},
                            "protein": {"value_computed": 2.5, "unit": "g"},
                        },
                    }
                },
            }
        },
        "12345678",
    )

    assert product.calories == 100
    assert product.carbohydrates == 1
    assert product.fat == 1
    assert product.protein == 2.5
    assert product.nutrition_basis == "serving"
    assert product.missing_nutrients == []


def test_parse_product_falls_back_to_generated_title_and_minimum_weight() -> None:
    product = parse_product(
        {
            "product": {
                "code": "87654321",
                "product_name": "   ",
                "brands": "",
                "serving_quantity": -10,
                "serving_quantity_unit": "g",
            }
        },
        "12345678",
    )

    assert product.title == "Product 87654321"
    assert product.brand is None
    assert product.weight_per_piece == 1


@pytest.mark.parametrize("payload", [{}, {"product": None}, {"product": []}])
def test_parse_product_requires_product_object(payload: dict[str, object]) -> None:
    with pytest.raises(ProductNotFoundError):
        parse_product(payload, "12345678")


def test_lookup_sends_identifying_user_agent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path.endswith("/12345678")
        assert request.headers["user-agent"]
        assert request.url.params["fields"]
        assert request.url.params["lc"] == "en"
        return httpx.Response(
            200,
            json={"product": {"code": "12345678", "product_name": "Test food"}},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = lookup_product("12345678", client)

    assert result.barcode == "12345678"


def test_lookup_handles_missing_product() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(404))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ProductNotFoundError):
            lookup_product("12345678", client)


def test_lookup_handles_success_response_without_product() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ProductNotFoundError):
            lookup_product("12345678", client)


@pytest.mark.parametrize("status_code", [400, 429, 500, 503])
def test_lookup_handles_upstream_error_status(status_code: int) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status_code, request=request)
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(OpenFoodFactsUnavailableError):
            lookup_product("12345678", client)


def test_lookup_handles_invalid_json() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"not-json", request=request)
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(OpenFoodFactsUnavailableError):
            lookup_product("12345678", client)


def test_lookup_handles_network_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Open Food Facts is unreachable", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OpenFoodFactsUnavailableError):
            lookup_product("12345678", client)
