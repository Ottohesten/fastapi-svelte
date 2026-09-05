from decimal import Decimal

import pytest

from app.quick_add import (
    CatalogCandidate,
    FoodSourceType,
    MealGroup,
    ParseStatus,
    QuantityUnit,
    parse_quick_add,
)

pytestmark = pytest.mark.no_db


@pytest.fixture
def catalog() -> tuple[CatalogCandidate, ...]:
    return (
        CatalogCandidate(
            id="recipe-oats",
            source_type=FoodSourceType.RECIPE,
            title="Havregrød",
            aliases=("Oatmeal",),
        ),
        CatalogCandidate(
            id="recipe-lasagna",
            source_type=FoodSourceType.RECIPE,
            title="Lasagna",
        ),
        CatalogCandidate(
            id="product-skyr",
            source_type=FoodSourceType.PRODUCT,
            title="Vanilla Skyr",
            aliases=("Vanilje skyr",),
        ),
        CatalogCandidate(
            id="ingredient-oil",
            source_type=FoodSourceType.INGREDIENT,
            title="Olive oil",
            aliases=("Olivenolie",),
        ),
    )


def test_parses_standalone_and_inline_bilingual_meal_headers(
    catalog: tuple[CatalogCandidate, ...],
) -> None:
    result = parse_quick_add(
        """
        Morgenmad:
        1,5 portioner opskrift: Havregrød
        Lunch: 1/2 servings recipe: Lasagna
        quarter serving Oatmeal
        """,
        catalog,
        MealGroup.SNACK,
    )

    assert result.can_confirm is True
    assert [draft.meal_group for draft in result.drafts] == [
        MealGroup.BREAKFAST,
        MealGroup.LUNCH,
        MealGroup.LUNCH,
    ]
    assert [draft.quantity for draft in result.drafts] == [
        Decimal("1.5"),
        Decimal("0.5"),
        Decimal("0.25"),
    ]
    assert all(draft.unit is QuantityUnit.SERVING for draft in result.drafts)
    resolved_candidates = [draft.resolved_candidate for draft in result.drafts]
    assert all(candidate is not None for candidate in resolved_candidates)
    assert [
        candidate.id for candidate in resolved_candidates if candidate is not None
    ] == [
        "recipe-oats",
        "recipe-lasagna",
        "recipe-oats",
    ]


def test_unprefixed_lines_use_default_meal_and_normalize_units(
    catalog: tuple[CatalogCandidate, ...],
) -> None:
    result = parse_quick_add(
        "0.25 kg Vanilla Skyr\nhalv L product: Vanilla Skyr\n2 stk Olivenolie",
        catalog,
        "dinner",
    )

    assert [draft.meal_group for draft in result.drafts] == [MealGroup.DINNER] * 3
    assert [(draft.quantity, draft.unit) for draft in result.drafts] == [
        (Decimal("250.00"), QuantityUnit.GRAM),
        (Decimal("500.0"), QuantityUnit.MILLILITER),
        (Decimal(2), QuantityUnit.PIECE),
    ]
    assert all(draft.status is ParseStatus.RESOLVED for draft in result.drafts)


def test_exact_alias_collision_is_ambiguous_until_qualified() -> None:
    candidates = (
        CatalogCandidate("recipe", FoodSourceType.RECIPE, "House pizza"),
        CatalogCandidate(
            "product", FoodSourceType.PRODUCT, "Frozen pizza", ("House pizza",)
        ),
    )

    ambiguous, qualified = parse_quick_add(
        "1 serving House pizza\n1 serving recipe: House pizza",
        candidates,
        "dinner",
    ).drafts

    assert ambiguous.status is ParseStatus.AMBIGUOUS
    assert {candidate.id for candidate in ambiguous.exact_matches} == {
        "recipe",
        "product",
    }
    assert ambiguous.resolved_candidate is None
    assert qualified.status is ParseStatus.RESOLVED
    assert qualified.resolved_candidate is not None
    assert qualified.resolved_candidate.id == "recipe"


def test_fuzzy_matches_are_suggestions_and_never_auto_resolve(
    catalog: tuple[CatalogCandidate, ...],
) -> None:
    (draft,) = parse_quick_add(
        "1 serving Lasagne", catalog, "dinner", suggestion_threshold=0.5
    ).drafts

    assert draft.status is ParseStatus.NEEDS_NUTRITION
    assert draft.resolved_candidate is None
    assert draft.exact_matches == ()
    assert draft.suggestions[0].candidate.id == "recipe-lasagna"
    assert draft.suggestions[0].similarity < 1


def test_source_qualifier_filters_fuzzy_suggestions() -> None:
    candidates = (
        CatalogCandidate("recipe", FoodSourceType.RECIPE, "Apple pie"),
        CatalogCandidate("product", FoodSourceType.PRODUCT, "Apple pies"),
    )

    (draft,) = parse_quick_add(
        "1 package product: Apple piy",
        candidates,
        "snack",
        suggestion_threshold=0.5,
    ).drafts

    assert draft.status is ParseStatus.NEEDS_NUTRITION
    assert [item.candidate.id for item in draft.suggestions] == ["product"]


def test_manual_entry_keeps_omitted_or_question_mark_macros_unknown() -> None:
    (draft,) = parse_quick_add(
        "Snack: engangs: Kanelsnegl | 420 kcal | kulhydrat 48,5 g | fedt ?",
        (),
        "breakfast",
    ).drafts

    assert draft.status is ParseStatus.RESOLVED
    assert draft.meal_group is MealGroup.SNACK
    assert draft.source_type is FoodSourceType.MANUAL
    assert draft.manual_nutrition is not None
    assert draft.manual_nutrition.calories == Decimal(420)
    assert draft.manual_nutrition.carbohydrates == Decimal("48.5")
    assert draft.manual_nutrition.fat is None
    assert draft.manual_nutrition.protein is None
    assert draft.manual_nutrition.missing_macros == ("fat", "protein")


def test_manual_entry_accepts_english_macros_in_any_order() -> None:
    (draft,) = parse_quick_add(
        "manual: Cafe cake | protein 6 g | 430 calories | fat 18 g | carbs 52 g",
        (),
        MealGroup.SNACK,
    ).drafts

    assert draft.status is ParseStatus.RESOLVED
    assert draft.manual_nutrition is not None
    assert draft.manual_nutrition.calories == Decimal(430)
    assert draft.manual_nutrition.carbohydrates == Decimal(52)
    assert draft.manual_nutrition.fat == Decimal(18)
    assert draft.manual_nutrition.protein == Decimal(6)
    assert draft.manual_nutrition.missing_macros == ()


@pytest.mark.parametrize(
    ("line", "error_code"),
    [
        ("I ate 200 g Vanilla Skyr", "invalid_format"),
        ("yesterday: 200 g Vanilla Skyr", "invalid_format"),
        ("200 oz Vanilla Skyr", "unsupported_unit"),
        ("0 g Vanilla Skyr", "invalid_quantity"),
        ("manual: Mystery snack | 200 kcal | sugar 4 g", "invalid_nutrition_segment"),
    ],
)
def test_rejects_prose_dates_estimates_and_invalid_nutrition(
    catalog: tuple[CatalogCandidate, ...], line: str, error_code: str
) -> None:
    (draft,) = parse_quick_add(line, catalog, "snack").drafts

    assert draft.status is ParseStatus.INVALID
    assert draft.error_code == error_code
    assert draft.resolved_candidate is None


def test_valid_lines_are_preserved_beside_invalid_and_unknown_lines(
    catalog: tuple[CatalogCandidate, ...],
) -> None:
    result = parse_quick_add(
        "1 serving Lasagna\nnot structured prose\n1 piece Cheeseburger",
        catalog,
        "lunch",
    )

    assert [draft.status for draft in result.drafts] == [
        ParseStatus.RESOLVED,
        ParseStatus.INVALID,
        ParseStatus.NEEDS_NUTRITION,
    ]
    assert result.can_confirm is False


def test_duplicate_candidate_rows_do_not_create_false_ambiguity() -> None:
    candidate = CatalogCandidate("same", FoodSourceType.PRODUCT, "Skyr")

    (draft,) = parse_quick_add(
        "200 gram skyr", (candidate, candidate), "breakfast"
    ).drafts

    assert draft.status is ParseStatus.RESOLVED
    assert draft.resolved_candidate is candidate


def test_conflicting_duplicate_candidate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="conflicting entries"):
        parse_quick_add(
            "1 serving Food",
            (
                CatalogCandidate("same", FoodSourceType.RECIPE, "First"),
                CatalogCandidate("same", FoodSourceType.RECIPE, "Second"),
            ),
            "lunch",
        )


def test_exact_name_without_quantity_is_ready_for_quantity_selection(
    catalog: tuple[CatalogCandidate, ...],
) -> None:
    (draft,) = parse_quick_add("opskrift: Havregrød", catalog, "breakfast").drafts

    assert draft.status is ParseStatus.NEEDS_QUANTITY
    assert draft.error_code == "missing_quantity"
    assert draft.name == "Havregrød"
    assert draft.quantity is None
    assert draft.unit is None
    assert draft.source_type is FoodSourceType.RECIPE
    assert draft.resolved_candidate is not None
    assert draft.resolved_candidate.id == "recipe-oats"


@pytest.mark.parametrize(
    "line", ["manual: Mystery snack", "manuel: Mystery snack | protein 2 g"]
)
def test_missing_calories_needs_nutrition_instead_of_being_malformed(
    line: str,
) -> None:
    (draft,) = parse_quick_add(line, (), "snack").drafts

    assert draft.status is ParseStatus.NEEDS_NUTRITION
    assert draft.error_code == "missing_calories"
    assert draft.name == "Mystery snack"
    assert draft.source_type is FoodSourceType.MANUAL
    assert draft.quantity == Decimal(1)
    assert draft.unit is QuantityUnit.PIECE


@pytest.mark.parametrize("zero", ["0", "0.0", "0,00", "0/2"])
def test_manual_nutrition_accepts_all_numeric_zero_forms(zero: str) -> None:
    (draft,) = parse_quick_add(
        f"manual: Water | {zero} kcal | carbs {zero} g | fat {zero} g | protein {zero} g",
        (),
        "snack",
    ).drafts

    assert draft.status is ParseStatus.RESOLVED
    assert draft.manual_nutrition is not None
    assert draft.manual_nutrition.calories == 0
    assert draft.manual_nutrition.carbohydrates == 0
    assert draft.manual_nutrition.fat == 0
    assert draft.manual_nutrition.protein == 0
    assert draft.manual_nutrition.missing_macros == ()


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("one", Decimal(1)),
        ("en", Decimal(1)),
        ("et", Decimal(1)),
        ("two", Decimal(2)),
        ("to", Decimal(2)),
        ("half", Decimal("0.5")),
        ("halv", Decimal("0.5")),
        ("quarter", Decimal("0.25")),
        ("kvart", Decimal("0.25")),
    ],
)
def test_approved_english_and_danish_number_words(
    catalog: tuple[CatalogCandidate, ...], amount: str, expected: Decimal
) -> None:
    (draft,) = parse_quick_add(
        f"{amount} portion opskrift: Havregrød", catalog, "breakfast"
    ).drafts

    assert draft.status is ParseStatus.RESOLVED
    assert draft.quantity == expected
    assert draft.unit is QuantityUnit.SERVING


def test_normalizes_unicode_danish_equivalents_accents_and_punctuation() -> None:
    candidates = (
        CatalogCandidate(
            "porridge",
            FoodSourceType.RECIPE,
            "Æble-grød",
            aliases=("Café grød",),
        ),
    )

    result = parse_quick_add(
        """
        Mellemmåltid:
        en servering Aeble groed!
        Snacks: et stk. Cafe grod
        """,
        candidates,
        "lunch",
    )

    assert result.can_confirm is True
    assert [draft.meal_group for draft in result.drafts] == [MealGroup.SNACK] * 2
    assert [draft.unit for draft in result.drafts] == [
        QuantityUnit.SERVING,
        QuantityUnit.PIECE,
    ]
    assert all(
        draft.resolved_candidate is not None
        and draft.resolved_candidate.id == "porridge"
        for draft in result.drafts
    )


def test_duplicate_catalog_rows_and_aliases_produce_one_suggestion() -> None:
    candidates = (
        CatalogCandidate(
            "skyr",
            FoodSourceType.PRODUCT,
            "Vanilla Skyr",
            aliases=("Vanilje-skyr", "Vanilje skyr"),
        ),
        CatalogCandidate(
            "skyr",
            FoodSourceType.PRODUCT,
            "Vanilla Skyr",
            aliases=("Skyr vanilla",),
        ),
    )

    (draft,) = parse_quick_add(
        "200 g Vanilla Sky", candidates, "breakfast", suggestion_threshold=0.5
    ).drafts

    assert draft.status is ParseStatus.NEEDS_NUTRITION
    assert len(draft.suggestions) == 1
    assert draft.suggestions[0].candidate.id == "skyr"
    assert set(draft.suggestions[0].candidate.aliases) == {
        "Vanilje-skyr",
        "Skyr vanilla",
    }


def test_exact_duplicate_names_without_quantity_remain_ambiguous() -> None:
    candidates = (
        CatalogCandidate("recipe", FoodSourceType.RECIPE, "Pizza"),
        CatalogCandidate("product", FoodSourceType.PRODUCT, "Pizza"),
    )

    (draft,) = parse_quick_add("Pizza", candidates, "dinner").drafts

    assert draft.status is ParseStatus.AMBIGUOUS
    assert draft.quantity is None
    assert {candidate.source_type for candidate in draft.exact_matches} == {
        FoodSourceType.RECIPE,
        FoodSourceType.PRODUCT,
    }


@pytest.mark.parametrize(
    ("stored_barcode", "entered_barcode"),
    [
        ("0123456789012", "123456789012"),
        ("00001234", "1234"),
        ("00000000", "0000"),
    ],
)
def test_exact_barcode_matching_uses_canonical_variants(
    stored_barcode: str, entered_barcode: str
) -> None:
    candidate = CatalogCandidate(
        "product",
        FoodSourceType.PRODUCT,
        "Barcode food",
        aliases=(stored_barcode,),
    )

    (draft,) = parse_quick_add(
        f"1 package {entered_barcode}", (candidate,), "snack"
    ).drafts

    assert draft.status is ParseStatus.RESOLVED
    assert draft.resolved_candidate is candidate
