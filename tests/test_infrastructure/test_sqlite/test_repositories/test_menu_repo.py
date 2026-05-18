import pytest
import sqlite3
from decimal import Decimal
from cafe_manager.infrastructure.db.sqlite.repository.menu_repo import SQLiteMenuRepo
from cafe_manager.domain.entities.menu import (
    MenuItem,
    Recipe,
    MenuItemCategory,
    Ingredient,
    Unit,
)
from cafe_manager.domain.entities.finance import Money


class TestSQLiteMenuRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test_menu.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteMenuRepo(conn)
        repo._init_db()

        yield repo
        conn.close()

    @pytest.fixture
    def sample_ingredient(self):
        return Ingredient("Milk", Unit.MILLILITER)

    @pytest.fixture
    def sample_item(self, sample_ingredient):
        recipe = Recipe(ingredients={sample_ingredient: 200.0})
        return MenuItem(
            name="Latte",
            recipe=recipe,
            price=Money(Decimal("7.50")),
            category=MenuItemCategory.COFFEE,
        )

    def test_save_and_get_by_name(self, repo, sample_item):
        repo.save(sample_item)

        retrieved = repo.get_by_name("Latte")
        assert retrieved is not None
        assert retrieved.name == "Latte"
        assert retrieved.price == Money(Decimal("7.50"))
        assert retrieved.category == MenuItemCategory.COFFEE
        assert retrieved.item_type == "drink"

        # Check recipe reconstruction
        assert len(retrieved.recipe.ingredients) == 1
        ing, amount = list(retrieved.recipe.ingredients.items())[0]
        assert ing.name == "Milk"
        assert ing.unit == Unit.MILLILITER
        assert amount == 200.0

    def test_save_overwrite_existing(self, repo, sample_item):
        repo.save(sample_item)

        updated_item = MenuItem(
            name="Latte",
            recipe=Recipe(ingredients={}),
            price=Money(Decimal("8.00")),
            category=MenuItemCategory.COFFEE,
        )
        repo.save(updated_item)

        retrieved = repo.get_by_name("Latte")
        assert retrieved.price == Money(Decimal("8.00"))
        assert len(retrieved.recipe.ingredients) == 0

    def test_get_all(self, repo, sample_item):
        item2 = MenuItem(
            name="Croissant",
            recipe=Recipe(ingredients={}),
            price=Money(Decimal("5.00")),
            category=MenuItemCategory.BAKERY,
        )
        repo.save(sample_item)
        repo.save(item2)

        all_items = repo.get_all()
        assert isinstance(all_items, set)
        assert len(all_items) == 2

        names = {i.name for i in all_items}
        assert "Latte" in names
        assert "Croissant" in names

    def test_delete_by_name(self, repo, sample_item):
        repo.save(sample_item)
        assert repo.get_by_name("Latte") is not None

        repo.delete_by_name("Latte")
        assert repo.get_by_name("Latte") is None

    def test_get_non_existent(self, repo):
        assert repo.get_by_name("Ghost Burger") is None

    def test_get_all_empty(self, repo):
        assert repo.get_all() is None

    def test_complex_recipe_roundtrip(self, repo):
        ing1 = Ingredient("Water", Unit.MILLILITER)
        ing2 = Ingredient("Sugar", Unit.GRAM)
        recipe = Recipe(ingredients={ing1: 100.0, ing2: 10.5})

        item = MenuItem(
            name="Sweet Water",
            recipe=recipe,
            price=Money(Decimal("1.00")),
            category=MenuItemCategory.COCKTAIL,
        )
        repo.save(item)

        retrieved = repo.get_by_name("Sweet Water")
        ingredients = retrieved.recipe.ingredients
        assert len(ingredients) == 2
        assert ingredients[ing1] == 100.0
        assert ingredients[ing2] == 10.5
