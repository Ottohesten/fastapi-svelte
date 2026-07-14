import httpx
import pytest

from app.openfoodfacts import (
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


def test_lookup_sends_identifying_user_agent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["user-agent"]
        assert request.url.params["fields"]
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
