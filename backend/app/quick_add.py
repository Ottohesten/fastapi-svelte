from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from enum import StrEnum


class MealGroup(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class FoodSourceType(StrEnum):
    RECIPE = "recipe"
    PRODUCT = "product"
    INGREDIENT = "ingredient"
    MANUAL = "manual"


class QuantityUnit(StrEnum):
    SERVING = "serving"
    GRAM = "g"
    MILLILITER = "ml"
    PIECE = "piece"
    PACKAGE = "package"


class ParseStatus(StrEnum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    NEEDS_QUANTITY = "needs_quantity"
    NEEDS_NUTRITION = "needs_nutrition"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class CatalogCandidate:
    """A food the caller is allowed to offer to the quick-add parser."""

    id: str
    source_type: FoodSourceType
    title: str
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", str(self.id).strip())
        object.__setattr__(self, "source_type", FoodSourceType(self.source_type))
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(
            self,
            "aliases",
            _deduplicate_names(self.aliases, excluded=(self.title,)),
        )
        if not self.id:
            raise ValueError("Catalog candidate id cannot be empty")
        if not self.title or not _name_variants(self.title):
            raise ValueError("Catalog candidate title cannot be empty")
        if self.source_type is FoodSourceType.MANUAL:
            raise ValueError("Manual entries are not catalog candidates")


@dataclass(frozen=True, slots=True)
class CatalogSuggestion:
    candidate: CatalogCandidate
    similarity: float


@dataclass(frozen=True, slots=True)
class ManualNutrition:
    calories: Decimal
    carbohydrates: Decimal | None = None
    fat: Decimal | None = None
    protein: Decimal | None = None

    @property
    def missing_macros(self) -> tuple[str, ...]:
        return tuple(
            name
            for name in ("carbohydrates", "fat", "protein")
            if getattr(self, name) is None
        )


@dataclass(frozen=True, slots=True)
class QuickAddDraft:
    line_number: int
    original_text: str
    meal_group: MealGroup
    status: ParseStatus
    name: str | None = None
    quantity: Decimal | None = None
    unit: QuantityUnit | None = None
    source_type: FoodSourceType | None = None
    resolved_candidate: CatalogCandidate | None = None
    exact_matches: tuple[CatalogCandidate, ...] = ()
    suggestions: tuple[CatalogSuggestion, ...] = ()
    manual_nutrition: ManualNutrition | None = None
    error_code: str | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class QuickAddParseResult:
    drafts: tuple[QuickAddDraft, ...]

    @property
    def can_confirm(self) -> bool:
        return bool(self.drafts) and all(
            draft.status is ParseStatus.RESOLVED for draft in self.drafts
        )


_MEAL_ALIASES = {
    "breakfast": MealGroup.BREAKFAST,
    "morgenmad": MealGroup.BREAKFAST,
    "lunch": MealGroup.LUNCH,
    "frokost": MealGroup.LUNCH,
    "dinner": MealGroup.DINNER,
    "aftensmad": MealGroup.DINNER,
    "snack": MealGroup.SNACK,
    "snacks": MealGroup.SNACK,
    "mellemmaltid": MealGroup.SNACK,
    "mellemmaaltid": MealGroup.SNACK,
    "mellemmaaltider": MealGroup.SNACK,
}

_SOURCE_ALIASES = {
    "recipe": FoodSourceType.RECIPE,
    "opskrift": FoodSourceType.RECIPE,
    "product": FoodSourceType.PRODUCT,
    "produkt": FoodSourceType.PRODUCT,
    "ingredient": FoodSourceType.INGREDIENT,
    "ingrediens": FoodSourceType.INGREDIENT,
    "manual": FoodSourceType.MANUAL,
    "manuel": FoodSourceType.MANUAL,
    "one off": FoodSourceType.MANUAL,
    "oneoff": FoodSourceType.MANUAL,
    "engangs": FoodSourceType.MANUAL,
    "engang": FoodSourceType.MANUAL,
}

_UNIT_ALIASES: dict[str, tuple[QuantityUnit, Decimal]] = {
    "serving": (QuantityUnit.SERVING, Decimal(1)),
    "servings": (QuantityUnit.SERVING, Decimal(1)),
    "portion": (QuantityUnit.SERVING, Decimal(1)),
    "portions": (QuantityUnit.SERVING, Decimal(1)),
    "portioner": (QuantityUnit.SERVING, Decimal(1)),
    "servering": (QuantityUnit.SERVING, Decimal(1)),
    "serveringer": (QuantityUnit.SERVING, Decimal(1)),
    "g": (QuantityUnit.GRAM, Decimal(1)),
    "gram": (QuantityUnit.GRAM, Decimal(1)),
    "grams": (QuantityUnit.GRAM, Decimal(1)),
    "grammer": (QuantityUnit.GRAM, Decimal(1)),
    "kg": (QuantityUnit.GRAM, Decimal(1000)),
    "kilo": (QuantityUnit.GRAM, Decimal(1000)),
    "kilos": (QuantityUnit.GRAM, Decimal(1000)),
    "kilogram": (QuantityUnit.GRAM, Decimal(1000)),
    "kilograms": (QuantityUnit.GRAM, Decimal(1000)),
    "ml": (QuantityUnit.MILLILITER, Decimal(1)),
    "milliliter": (QuantityUnit.MILLILITER, Decimal(1)),
    "milliliters": (QuantityUnit.MILLILITER, Decimal(1)),
    "millilitre": (QuantityUnit.MILLILITER, Decimal(1)),
    "millilitres": (QuantityUnit.MILLILITER, Decimal(1)),
    "l": (QuantityUnit.MILLILITER, Decimal(1000)),
    "liter": (QuantityUnit.MILLILITER, Decimal(1000)),
    "liters": (QuantityUnit.MILLILITER, Decimal(1000)),
    "litre": (QuantityUnit.MILLILITER, Decimal(1000)),
    "litres": (QuantityUnit.MILLILITER, Decimal(1000)),
    "unit": (QuantityUnit.PIECE, Decimal(1)),
    "units": (QuantityUnit.PIECE, Decimal(1)),
    "piece": (QuantityUnit.PIECE, Decimal(1)),
    "pieces": (QuantityUnit.PIECE, Decimal(1)),
    "pc": (QuantityUnit.PIECE, Decimal(1)),
    "pcs": (QuantityUnit.PIECE, Decimal(1)),
    "stk": (QuantityUnit.PIECE, Decimal(1)),
    "styk": (QuantityUnit.PIECE, Decimal(1)),
    "stykke": (QuantityUnit.PIECE, Decimal(1)),
    "stykker": (QuantityUnit.PIECE, Decimal(1)),
    "package": (QuantityUnit.PACKAGE, Decimal(1)),
    "packages": (QuantityUnit.PACKAGE, Decimal(1)),
    "pack": (QuantityUnit.PACKAGE, Decimal(1)),
    "packs": (QuantityUnit.PACKAGE, Decimal(1)),
    "pakke": (QuantityUnit.PACKAGE, Decimal(1)),
    "pakker": (QuantityUnit.PACKAGE, Decimal(1)),
}

_NUMBER_WORDS = {
    "half": Decimal("0.5"),
    "halv": Decimal("0.5"),
    "quarter": Decimal("0.25"),
    "kvart": Decimal("0.25"),
    "one": Decimal(1),
    "en": Decimal(1),
    "et": Decimal(1),
    "two": Decimal(2),
    "to": Decimal(2),
}

_NUMBER_PATTERN = (
    r"(?:\d+\s*/\s*\d+|\d+(?:[.,]\d+)?|"
    r"half|halv|quarter|kvart|one|en|et|two|to)"
)
_CATALOG_LINE = re.compile(
    rf"^(?P<quantity>{_NUMBER_PATTERN})\s+(?P<unit>\S+)\s+(?P<name>.+)$",
    flags=re.IGNORECASE,
)
_CALORIE_SEGMENT = re.compile(
    rf"^(?P<value>{_NUMBER_PATTERN})\s*(?:kcal|calories|kalorier)$",
    flags=re.IGNORECASE,
)
_MACRO_SEGMENT = re.compile(
    rf"^(?P<name>[\wæøåÆØÅ-]+)\s+(?P<value>{_NUMBER_PATTERN}|\?)"
    r"(?:\s*(?:g|gram|grams|grammer))?$",
    flags=re.IGNORECASE,
)
_MACRO_ALIASES = {
    "carb": "carbohydrates",
    "carbs": "carbohydrates",
    "carbohydrate": "carbohydrates",
    "carbohydrates": "carbohydrates",
    "kulhydrat": "carbohydrates",
    "kulhydrater": "carbohydrates",
    "fat": "fat",
    "fedt": "fat",
    "protein": "protein",
    "proteins": "protein",
    "proteiner": "protein",
}

_DANISH_TRANSLITERATION = str.maketrans(
    {"\u00e6": "ae", "\u00f8": "oe", "\u00e5": "aa"}
)
_DANISH_SIMPLIFICATION = str.maketrans({"\u00e6": "a", "\u00f8": "o", "\u00e5": "a"})


def parse_quick_add(
    text: str,
    candidates: Iterable[CatalogCandidate],
    default_meal_group: MealGroup | str,
    *,
    suggestion_limit: int = 3,
    suggestion_threshold: float = 0.6,
) -> QuickAddParseResult:
    """Parse the deliberately small quick-add language without persisting anything."""

    if suggestion_limit < 0:
        raise ValueError("suggestion_limit cannot be negative")
    if not 0 <= suggestion_threshold <= 1:
        raise ValueError("suggestion_threshold must be between 0 and 1")

    meal_group = MealGroup(default_meal_group)
    catalog = _deduplicate_candidates(candidates)
    drafts: list[QuickAddDraft] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        inline_meal, remainder = _consume_qualifier(line, _MEAL_ALIASES)
        if inline_meal is not None:
            meal_group = inline_meal
            if not remainder:
                continue
            line = remainder

        source_qualifier, remainder = _consume_qualifier(line, _SOURCE_ALIASES)
        if source_qualifier is FoodSourceType.MANUAL:
            drafts.append(
                _parse_manual_line(
                    remainder,
                    line_number=line_number,
                    original_text=raw_line,
                    meal_group=meal_group,
                )
            )
            continue

        drafts.append(
            _parse_catalog_line(
                remainder if source_qualifier is not None else line,
                line_number=line_number,
                original_text=raw_line,
                meal_group=meal_group,
                source_qualifier=source_qualifier,
                catalog=catalog,
                suggestion_limit=suggestion_limit,
                suggestion_threshold=suggestion_threshold,
            )
        )

    return QuickAddParseResult(drafts=tuple(drafts))


def _parse_catalog_line(
    line: str,
    *,
    line_number: int,
    original_text: str,
    meal_group: MealGroup,
    source_qualifier: FoodSourceType | None,
    catalog: tuple[CatalogCandidate, ...],
    suggestion_limit: int,
    suggestion_threshold: float,
) -> QuickAddDraft:
    match = _CATALOG_LINE.fullmatch(line)
    if not match:
        name = line.strip()
        if not name:
            return _invalid_draft(
                line_number,
                original_text,
                meal_group,
                "missing_name",
                "Food name cannot be empty.",
            )

        pool = _filter_catalog(catalog, source_qualifier)
        exact_matches = _exact_matches(name, pool)
        if len(exact_matches) == 1:
            candidate = exact_matches[0]
            return QuickAddDraft(
                line_number=line_number,
                original_text=original_text,
                meal_group=meal_group,
                status=ParseStatus.NEEDS_QUANTITY,
                name=name,
                source_type=candidate.source_type,
                resolved_candidate=candidate,
                exact_matches=exact_matches,
                error_code="missing_quantity",
                message="Choose an amount and unit before adding this food.",
            )
        if len(exact_matches) > 1:
            return QuickAddDraft(
                line_number=line_number,
                original_text=original_text,
                meal_group=meal_group,
                status=ParseStatus.AMBIGUOUS,
                name=name,
                source_type=source_qualifier,
                exact_matches=exact_matches,
                error_code="ambiguous_food",
                message="More than one catalog item has that exact name.",
            )
        return _invalid_draft(
            line_number,
            original_text,
            meal_group,
            "invalid_format",
            "Use one item per line in the form '<amount> <unit> <food name>'.",
        )

    try:
        quantity = _parse_number(match.group("quantity"))
    except ValueError as exc:
        return _invalid_draft(
            line_number,
            original_text,
            meal_group,
            "invalid_quantity",
            str(exc),
        )

    raw_unit = _normalize_keyword(match.group("unit"))
    unit_conversion = _UNIT_ALIASES.get(raw_unit)
    if unit_conversion is None:
        return _invalid_draft(
            line_number,
            original_text,
            meal_group,
            "unsupported_unit",
            f"Unsupported quantity unit: {match.group('unit')}",
        )
    unit, factor = unit_conversion
    quantity *= factor

    name = match.group("name").strip()
    inline_source, remainder = _consume_qualifier(name, _SOURCE_ALIASES)
    if inline_source is FoodSourceType.MANUAL:
        return _invalid_draft(
            line_number,
            original_text,
            meal_group,
            "invalid_source_qualifier",
            "Manual entries use 'manual: <name> | <calories> kcal'.",
        )
    if inline_source is not None:
        if source_qualifier is not None:
            return _invalid_draft(
                line_number,
                original_text,
                meal_group,
                "duplicate_source_qualifier",
                "Use at most one source qualifier per line.",
            )
        source_qualifier = inline_source
        name = remainder

    if not name:
        return _invalid_draft(
            line_number,
            original_text,
            meal_group,
            "missing_name",
            "Food name cannot be empty.",
        )

    requested_names = _name_variants(name)
    if not requested_names:
        return _invalid_draft(
            line_number,
            original_text,
            meal_group,
            "invalid_name",
            "Food name must contain a letter or number.",
        )
    pool = _filter_catalog(catalog, source_qualifier)
    exact_matches = _exact_matches(name, pool)

    if len(exact_matches) == 1:
        candidate = exact_matches[0]
        return QuickAddDraft(
            line_number=line_number,
            original_text=original_text,
            meal_group=meal_group,
            status=ParseStatus.RESOLVED,
            name=name,
            quantity=quantity,
            unit=unit,
            source_type=candidate.source_type,
            resolved_candidate=candidate,
            exact_matches=exact_matches,
        )
    if len(exact_matches) > 1:
        return QuickAddDraft(
            line_number=line_number,
            original_text=original_text,
            meal_group=meal_group,
            status=ParseStatus.AMBIGUOUS,
            name=name,
            quantity=quantity,
            unit=unit,
            source_type=source_qualifier,
            exact_matches=exact_matches,
            error_code="ambiguous_food",
            message="More than one catalog item has that exact name.",
        )

    suggestions = _suggest_candidates(
        requested_names,
        pool,
        limit=suggestion_limit,
        threshold=suggestion_threshold,
    )
    return QuickAddDraft(
        line_number=line_number,
        original_text=original_text,
        meal_group=meal_group,
        status=ParseStatus.NEEDS_NUTRITION,
        name=name,
        quantity=quantity,
        unit=unit,
        source_type=source_qualifier,
        suggestions=suggestions,
        error_code="unknown_food",
        message=(
            "Choose a suggested catalog item or provide manual nutrition before "
            "adding this food."
        ),
    )


def _parse_manual_line(
    line: str,
    *,
    line_number: int,
    original_text: str,
    meal_group: MealGroup,
) -> QuickAddDraft:
    segments = [segment.strip() for segment in line.split("|")]
    if not segments[0]:
        return _invalid_draft(
            line_number,
            original_text,
            meal_group,
            "invalid_manual_entry",
            "Use 'manual: <name> | <calories> kcal' for a one-off entry.",
        )

    name = segments[0]
    if len(segments) == 1:
        return _manual_needs_nutrition_draft(
            line_number=line_number,
            original_text=original_text,
            meal_group=meal_group,
            name=name,
        )

    calories: Decimal | None = None
    macros: dict[str, Decimal | None] = {
        "carbohydrates": None,
        "fat": None,
        "protein": None,
    }
    seen_macros: set[str] = set()

    for segment in segments[1:]:
        calorie_match = _CALORIE_SEGMENT.fullmatch(segment)
        if calorie_match:
            if calories is not None:
                return _invalid_manual_draft(
                    line_number,
                    original_text,
                    meal_group,
                    "duplicate_calories",
                    "Calories can only be provided once.",
                    name,
                )
            try:
                calories = _parse_nonnegative_number(calorie_match.group("value"))
            except ValueError as exc:
                return _invalid_manual_draft(
                    line_number,
                    original_text,
                    meal_group,
                    "invalid_calories",
                    str(exc),
                    name,
                )
            continue

        macro_match = _MACRO_SEGMENT.fullmatch(segment)
        if not macro_match:
            return _invalid_manual_draft(
                line_number,
                original_text,
                meal_group,
                "invalid_nutrition_segment",
                f"Unrecognized nutrition segment: {segment}",
                name,
            )
        macro_name = _MACRO_ALIASES.get(_normalize_keyword(macro_match.group("name")))
        if macro_name is None:
            return _invalid_manual_draft(
                line_number,
                original_text,
                meal_group,
                "invalid_nutrition_segment",
                f"Unrecognized nutrient: {macro_match.group('name')}",
                name,
            )
        if macro_name in seen_macros:
            return _invalid_manual_draft(
                line_number,
                original_text,
                meal_group,
                "duplicate_macro",
                f"{macro_name.capitalize()} can only be provided once.",
                name,
            )
        seen_macros.add(macro_name)
        raw_value = macro_match.group("value")
        if raw_value != "?":
            try:
                macros[macro_name] = _parse_nonnegative_number(raw_value)
            except ValueError as exc:
                return _invalid_manual_draft(
                    line_number,
                    original_text,
                    meal_group,
                    "invalid_macro",
                    str(exc),
                    name,
                )

    if calories is None:
        return _manual_needs_nutrition_draft(
            line_number=line_number,
            original_text=original_text,
            meal_group=meal_group,
            name=name,
        )

    return QuickAddDraft(
        line_number=line_number,
        original_text=original_text,
        meal_group=meal_group,
        status=ParseStatus.RESOLVED,
        name=name,
        quantity=Decimal(1),
        unit=QuantityUnit.PIECE,
        source_type=FoodSourceType.MANUAL,
        manual_nutrition=ManualNutrition(calories=calories, **macros),
    )


def _parse_number(raw_value: str) -> Decimal:
    return _parse_decimal(raw_value, allow_zero=False)


def _parse_nonnegative_number(raw_value: str) -> Decimal:
    return _parse_decimal(raw_value, allow_zero=True)


def _parse_decimal(raw_value: str, *, allow_zero: bool) -> Decimal:
    normalized = _normalize_token(raw_value)
    word_value = _NUMBER_WORDS.get(_normalize_keyword(normalized))
    if word_value is not None:
        return word_value

    try:
        if "/" in normalized:
            numerator, denominator = normalized.split("/", maxsplit=1)
            value = Decimal(numerator.strip()) / Decimal(denominator.strip())
        else:
            value = Decimal(normalized.replace(",", "."))
    except (InvalidOperation, ZeroDivisionError) as exc:
        raise ValueError("Quantity must be a valid number.") from exc
    if not value.is_finite() or value < 0 or (value == 0 and not allow_zero):
        comparator = "non-negative" if allow_zero else "greater than zero"
        raise ValueError(f"Value must be {comparator}.")
    return value


def _consume_qualifier[T: StrEnum](
    line: str, aliases: dict[str, T]
) -> tuple[T | None, str]:
    prefix, separator, remainder = line.partition(":")
    if not separator:
        return None, line
    qualifier = aliases.get(_normalize_keyword(prefix))
    if qualifier is None:
        return None, line
    return qualifier, remainder.strip()


def _candidate_names(candidate: CatalogCandidate) -> frozenset[str]:
    names: set[str] = set()
    for value in (candidate.title, *candidate.aliases):
        names.update(_name_variants(value))
    return frozenset(names)


def _filter_catalog(
    catalog: tuple[CatalogCandidate, ...],
    source_qualifier: FoodSourceType | None,
) -> tuple[CatalogCandidate, ...]:
    return tuple(
        candidate
        for candidate in catalog
        if source_qualifier is None or candidate.source_type is source_qualifier
    )


def _exact_matches(
    requested_name: str, candidates: tuple[CatalogCandidate, ...]
) -> tuple[CatalogCandidate, ...]:
    requested_names = _name_variants(requested_name)
    return tuple(
        candidate
        for candidate in candidates
        if requested_names.intersection(_candidate_names(candidate))
    )


def _deduplicate_candidates(
    candidates: Iterable[CatalogCandidate],
) -> tuple[CatalogCandidate, ...]:
    unique: dict[tuple[FoodSourceType, str], CatalogCandidate] = {}
    for candidate in candidates:
        key = (candidate.source_type, candidate.id)
        existing = unique.get(key)
        if existing is None:
            unique[key] = candidate
            continue
        if not _name_variants(existing.title).intersection(
            _name_variants(candidate.title)
        ):
            raise ValueError(
                "Catalog contains conflicting entries for "
                f"{candidate.source_type}:{candidate.id}"
            )
        aliases = _deduplicate_names(
            (*existing.aliases, candidate.title, *candidate.aliases),
            excluded=(existing.title,),
        )
        if aliases != existing.aliases:
            unique[key] = CatalogCandidate(
                id=existing.id,
                source_type=existing.source_type,
                title=existing.title,
                aliases=aliases,
            )
    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                _normalize_name(item.title),
                item.source_type.value,
                item.id,
            ),
        )
    )


def _suggest_candidates(
    requested_names: frozenset[str],
    candidates: tuple[CatalogCandidate, ...],
    *,
    limit: int,
    threshold: float,
) -> tuple[CatalogSuggestion, ...]:
    if limit == 0:
        return ()
    scored_by_candidate: dict[tuple[FoodSourceType, str], CatalogSuggestion] = {}
    for candidate in candidates:
        similarity = max(
            SequenceMatcher(None, requested_name, candidate_name).ratio()
            for requested_name in requested_names
            for candidate_name in _candidate_names(candidate)
        )
        if similarity >= threshold:
            suggestion = CatalogSuggestion(candidate, round(similarity, 4))
            key = (candidate.source_type, candidate.id)
            existing = scored_by_candidate.get(key)
            if existing is None or suggestion.similarity > existing.similarity:
                scored_by_candidate[key] = suggestion
    scored = list(scored_by_candidate.values())
    scored.sort(
        key=lambda item: (
            -item.similarity,
            _normalize_name(item.candidate.title),
            item.candidate.source_type.value,
            item.candidate.id,
        )
    )
    return tuple(scored[:limit])


def _invalid_draft(
    line_number: int,
    original_text: str,
    meal_group: MealGroup,
    error_code: str,
    message: str,
) -> QuickAddDraft:
    return QuickAddDraft(
        line_number=line_number,
        original_text=original_text,
        meal_group=meal_group,
        status=ParseStatus.INVALID,
        error_code=error_code,
        message=message,
    )


def _invalid_manual_draft(
    line_number: int,
    original_text: str,
    meal_group: MealGroup,
    error_code: str,
    message: str,
    name: str,
) -> QuickAddDraft:
    return QuickAddDraft(
        line_number=line_number,
        original_text=original_text,
        meal_group=meal_group,
        status=ParseStatus.INVALID,
        name=name,
        source_type=FoodSourceType.MANUAL,
        error_code=error_code,
        message=message,
    )


def _manual_needs_nutrition_draft(
    *,
    line_number: int,
    original_text: str,
    meal_group: MealGroup,
    name: str,
) -> QuickAddDraft:
    return QuickAddDraft(
        line_number=line_number,
        original_text=original_text,
        meal_group=meal_group,
        status=ParseStatus.NEEDS_NUTRITION,
        name=name,
        quantity=Decimal(1),
        unit=QuantityUnit.PIECE,
        source_type=FoodSourceType.MANUAL,
        error_code="missing_calories",
        message="Enter calories in kcal before adding this manual food.",
    )


def _normalize_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.translate(_DANISH_TRANSLITERATION)
    normalized = "".join(
        character
        for character in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(character)
    )
    return " ".join(normalized.split())


def _normalize_name(value: str) -> str:
    normalized = _normalize_token(value)
    without_punctuation = "".join(
        character if character.isalnum() else " " for character in normalized
    )
    return " ".join(without_punctuation.split())


def _normalize_keyword(value: str) -> str:
    return _normalize_name(value)


def _name_variants(value: str) -> frozenset[str]:
    normalized_name = _normalize_name(value)
    variants = {normalized_name}
    if normalized_name.isdigit() and 4 <= len(normalized_name) <= 24:
        significant = normalized_name.lstrip("0") or "0"
        if len(significant) <= 7:
            variants.add(significant.zfill(8))
        elif 9 <= len(significant) <= 12:
            variants.add(significant.zfill(13))
    casefolded = unicodedata.normalize("NFKC", value).casefold()
    if any(character in casefolded for character in "æøå"):
        variants.add(_normalize_name(casefolded.translate(_DANISH_SIMPLIFICATION)))
    return frozenset(variant for variant in variants if variant)


def _deduplicate_names(
    names: Iterable[str], *, excluded: Iterable[str] = ()
) -> tuple[str, ...]:
    seen: set[str] = set()
    for name in excluded:
        seen.update(_name_variants(name))

    unique: list[str] = []
    for name in names:
        stripped = name.strip()
        variants = _name_variants(stripped)
        if not stripped or not variants or variants.intersection(seen):
            continue
        unique.append(stripped)
        seen.update(variants)
    return tuple(unique)
