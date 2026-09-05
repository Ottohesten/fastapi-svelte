"""Add personal products and nutrition diary entries.

Revision ID: c8e4f1a2b6d9
Revises: b4d9a6e3c8f2
Create Date: 2026-09-03 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8e4f1a2b6d9"
down_revision: str | None = "b4d9a6e3c8f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("barcode", sa.String(length=24), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("carbohydrates", sa.Float(), nullable=True),
        sa.Column("fat", sa.Float(), nullable=True),
        sa.Column("protein", sa.Float(), nullable=True),
        sa.Column("serving_size", sa.Float(), nullable=True),
        sa.Column("package_size", sa.Float(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("nutrition_basis", sa.String(length=20), nullable=False),
        sa.Column("serving_size_unit", sa.String(length=2), nullable=True),
        sa.Column("package_size_unit", sa.String(length=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "calories >= 0 AND calories < 'Infinity'::double precision",
            name="ck_product_calories_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "carbohydrates IS NULL OR (carbohydrates >= 0 AND "
            "carbohydrates < 'Infinity'::double precision)",
            name="ck_product_carbohydrates_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "fat IS NULL OR (fat >= 0 AND fat < 'Infinity'::double precision)",
            name="ck_product_fat_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "protein IS NULL OR (protein >= 0 AND "
            "protein < 'Infinity'::double precision)",
            name="ck_product_protein_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "((serving_size IS NULL AND serving_size_unit IS NULL) OR "
            "(serving_size > 0 AND serving_size < 'Infinity'::double precision "
            "AND serving_size_unit IS NOT NULL))",
            name="ck_product_serving_size_pair",
        ),
        sa.CheckConstraint(
            "((package_size IS NULL AND package_size_unit IS NULL) OR "
            "(package_size > 0 AND package_size < 'Infinity'::double precision "
            "AND package_size_unit IS NOT NULL))",
            name="ck_product_package_size_pair",
        ),
        sa.CheckConstraint(
            "nutrition_basis IN ('per_100g', 'per_100ml', 'per_serving', "
            "'per_package')",
            name="ck_product_nutrition_basis",
        ),
        sa.CheckConstraint(
            "serving_size_unit IS NULL OR serving_size_unit IN ('g', 'ml')",
            name="ck_product_serving_size_unit",
        ),
        sa.CheckConstraint(
            "package_size_unit IS NULL OR package_size_unit IN ('g', 'ml')",
            name="ck_product_package_size_unit",
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "barcode", name="uq_product_owner_barcode"),
    )
    op.create_index(
        "ix_product_owner_title", "product", ["owner_id", "title"], unique=False
    )

    op.create_table(
        "nutritionentry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(length=16), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("recipe_id", sa.Uuid(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("ingredient_id", sa.Uuid(), nullable=True),
        sa.Column("title_snapshot", sa.String(length=255), nullable=False),
        sa.Column("brand_snapshot", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("carbohydrates", sa.Float(), nullable=True),
        sa.Column("fat", sa.Float(), nullable=True),
        sa.Column("protein", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "quantity > 0 AND quantity < 'Infinity'::double precision",
            name="ck_nutrition_entry_quantity_finite_positive",
        ),
        sa.CheckConstraint(
            "calories >= 0 AND calories < 'Infinity'::double precision",
            name="ck_nutrition_entry_calories_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "carbohydrates IS NULL OR (carbohydrates >= 0 AND "
            "carbohydrates < 'Infinity'::double precision)",
            name="ck_nutrition_entry_carbohydrates_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "fat IS NULL OR (fat >= 0 AND fat < 'Infinity'::double precision)",
            name="ck_nutrition_entry_fat_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "protein IS NULL OR (protein >= 0 AND "
            "protein < 'Infinity'::double precision)",
            name="ck_nutrition_entry_protein_finite_nonnegative",
        ),
        sa.CheckConstraint(
            "((CASE WHEN recipe_id IS NULL THEN 0 ELSE 1 END) + "
            "(CASE WHEN product_id IS NULL THEN 0 ELSE 1 END) + "
            "(CASE WHEN ingredient_id IS NULL THEN 0 ELSE 1 END)) <= 1",
            name="ck_nutrition_entry_at_most_one_source",
        ),
        sa.CheckConstraint(
            "recipe_id IS NULL OR source_type = 'recipe'",
            name="ck_nutrition_entry_recipe_source",
        ),
        sa.CheckConstraint(
            "product_id IS NULL OR source_type = 'product'",
            name="ck_nutrition_entry_product_source",
        ),
        sa.CheckConstraint(
            "ingredient_id IS NULL OR source_type = 'ingredient'",
            name="ck_nutrition_entry_ingredient_source",
        ),
        sa.CheckConstraint(
            "source_type != 'manual' OR "
            "(recipe_id IS NULL AND product_id IS NULL AND ingredient_id IS NULL)",
            name="ck_nutrition_entry_manual_has_no_source",
        ),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_nutrition_entry_meal_type",
        ),
        sa.CheckConstraint(
            "source_type IN ('recipe', 'product', 'ingredient', 'manual')",
            name="ck_nutrition_entry_source_type",
        ),
        sa.CheckConstraint(
            "unit IN ('serving', 'g', 'ml', 'piece', 'package')",
            name="ck_nutrition_entry_unit",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"], ["ingredient.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipe.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_nutrition_entry_owner_date_meal_created",
        "nutritionentry",
        ["owner_id", "log_date", "meal_type", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_nutrition_entry_owner_date_meal_created",
        table_name="nutritionentry",
    )
    op.drop_table("nutritionentry")
    op.drop_index("ix_product_owner_title", table_name="product")
    op.drop_table("product")
