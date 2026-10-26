from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Security, status
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select

from app.deps import SessionDep, get_current_user
from app.models import (
    Product,
    ProductBarcodePreviewPublic,
    ProductCreate,
    ProductPublic,
    ProductUpdate,
    User,
    normalize_food_barcode,
)
from app.openfoodfacts import (
    OpenFoodFactsUnavailableError,
    ProductNotFoundError,
    UnsupportedNutritionBasisError,
    lookup_product_draft,
)

router = APIRouter(prefix="/products", tags=["products"])


def _owned_product(session: SessionDep, product_id: uuid.UUID, user: User) -> Product:
    product = session.exec(
        select(Product).where(
            Product.id == product_id,
            Product.owner_id == user.id,
        )
    ).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _commit_product(session: SessionDep, product: Product) -> Product:
    session.add(product)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this barcode already exists",
        ) from exc
    session.refresh(product)
    return product


@router.get("/", response_model=list[ProductPublic])
def get_products(
    session: SessionDep,
    query: str | None = Query(default=None, max_length=255),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    statement = select(Product).where(Product.owner_id == current_user.id)
    if query and query.strip():
        search = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                col(Product.title).ilike(search),
                col(Product.brand).ilike(search),
                col(Product.barcode).ilike(search),
            )
        )
    statement = (
        statement.order_by(col(Product.title), col(Product.created_at))
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get("/barcode/{barcode}", response_model=ProductBarcodePreviewPublic)
def get_product_by_barcode(
    session: SessionDep,
    barcode: str,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    try:
        normalized_barcode = normalize_food_barcode(barcode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if normalized_barcode is None:
        raise HTTPException(status_code=422, detail="Barcode is required")

    existing = session.exec(
        select(Product).where(
            Product.owner_id == current_user.id,
            Product.barcode == normalized_barcode,
        )
    ).first()
    if existing is not None:
        missing_nutrients = [
            name
            for name in ("carbohydrates", "fat", "protein")
            if getattr(existing, name) is None
        ]
        return ProductBarcodePreviewPublic(
            barcode=normalized_barcode,
            title=existing.title,
            brand=existing.brand,
            image_url=existing.image_url,
            nutrition_basis=existing.nutrition_basis,
            calories=existing.calories,
            carbohydrates=existing.carbohydrates,
            fat=existing.fat,
            protein=existing.protein,
            serving_size=existing.serving_size,
            serving_size_unit=existing.serving_size_unit,
            package_size=existing.package_size,
            package_size_unit=existing.package_size_unit,
            missing_nutrients=missing_nutrients,
            needs_review=False,
            existing_product_id=existing.id,
        )

    try:
        preview = lookup_product_draft(normalized_barcode)
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="Product not found in Open Food Facts"
        ) from exc
    except OpenFoodFactsUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Open Food Facts is temporarily unavailable. Please try again.",
        ) from exc
    except UnsupportedNutritionBasisError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "Open Food Facts reported nutrition with an unsupported or missing "
                "basis. Enter this product manually."
            ),
        ) from exc

    return preview


@router.get("/{product_id}", response_model=ProductPublic)
def get_product(
    session: SessionDep,
    product_id: uuid.UUID,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    return _owned_product(session, product_id, current_user)


@router.post("/", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
def create_product(
    session: SessionDep,
    product_in: ProductCreate,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    product = Product.model_validate(product_in, update={"owner_id": current_user.id})
    return _commit_product(session, product)


@router.patch("/{product_id}", response_model=ProductPublic)
def update_product(
    session: SessionDep,
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    product = _owned_product(session, product_id, current_user)
    current_data = {name: getattr(product, name) for name in ProductCreate.model_fields}
    current_data.update(product_in.model_dump(exclude_unset=True))
    try:
        validated = ProductCreate.model_validate(current_data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=exc.errors(include_context=False)
        ) from exc
    product.sqlmodel_update(validated.model_dump())
    product.updated_at = datetime.now(UTC)
    return _commit_product(session, product)


@router.delete("/{product_id}", response_model=ProductPublic)
def delete_product(
    session: SessionDep,
    product_id: uuid.UUID,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    product = _owned_product(session, product_id, current_user)
    response = ProductPublic.model_validate(product)
    session.delete(product)
    session.commit()
    return response
