"""add recipes and recipe_materials tables

Revision ID: 5ed80f2548af
Revises: f4e5d6c7b8a9
Create Date: 2026-08-16 16:20:16.558367

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5ed80f2548af"
down_revision: Union[str, Sequence[str], None] = "f4e5d6c7b8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # =========================
    # CREATE RECIPES TABLE
    # =========================
    op.create_table(
        "recipes",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True
        ),
        sa.Column(
            "image",
            sa.String(length=255),
            nullable=True
        ),
        sa.Column(
            "category_id",
            sa.String(length=36),
            nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"]
        ),

        sa.PrimaryKeyConstraint("id")
    )

    # INDEX RECIPES
    op.create_index(
        op.f("ix_recipes_id"),
        "recipes",
        ["id"],
        unique=False
    )

    op.create_index(
        op.f("ix_recipes_title"),
        "recipes",
        ["title"],
        unique=False
    )

    op.create_index(
        op.f("ix_recipes_category_id"),
        "recipes",
        ["category_id"],
        unique=False
    )

    # =========================
    # CREATE RECIPE MATERIALS TABLE
    # =========================
    op.create_table(
        "recipe_materials",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False
        ),
        sa.Column(
            "recipe_id",
            sa.String(length=36),
            nullable=False
        ),
        sa.Column(
            "category_id",
            sa.String(length=36),
            nullable=False
        ),
        sa.Column(
            "material_name",
            sa.String(length=150),
            nullable=False
        ),
        sa.Column(
            "quantity_needed",
            sa.Float(),
            nullable=False
        ),
        sa.Column(
            "unit",
            sa.String(length=30),
            nullable=True
        ),
        sa.Column(
            "note",
            sa.String(length=255),
            nullable=True
        ),
        sa.Column(
            "suggested_product_id",
            sa.String(length=36),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"]
        ),

        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"]
        ),

        sa.ForeignKeyConstraint(
            ["suggested_product_id"],
            ["products.id"]
        ),

        sa.PrimaryKeyConstraint("id")
    )

    # INDEX RECIPE MATERIALS
    op.create_index(
        op.f("ix_recipe_materials_id"),
        "recipe_materials",
        ["id"],
        unique=False
    )

    op.create_index(
        op.f("ix_recipe_materials_recipe_id"),
        "recipe_materials",
        ["recipe_id"],
        unique=False
    )

    op.create_index(
        op.f("ix_recipe_materials_category_id"),
        "recipe_materials",
        ["category_id"],
        unique=False
    )

    op.create_index(
        op.f("ix_recipe_materials_suggested_product_id"),
        "recipe_materials",
        ["suggested_product_id"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    # =========================
    # DROP RECIPE MATERIALS
    # =========================
    op.drop_index(
        op.f("ix_recipe_materials_suggested_product_id"),
        table_name="recipe_materials"
    )

    op.drop_index(
        op.f("ix_recipe_materials_category_id"),
        table_name="recipe_materials"
    )

    op.drop_index(
        op.f("ix_recipe_materials_recipe_id"),
        table_name="recipe_materials"
    )

    op.drop_index(
        op.f("ix_recipe_materials_id"),
        table_name="recipe_materials"
    )

    op.drop_table("recipe_materials")

    # =========================
    # DROP RECIPES
    # =========================
    op.drop_index(
        op.f("ix_recipes_category_id"),
        table_name="recipes"
    )

    op.drop_index(
        op.f("ix_recipes_title"),
        table_name="recipes"
    )

    op.drop_index(
        op.f("ix_recipes_id"),
        table_name="recipes"
    )

    op.drop_table("recipes")