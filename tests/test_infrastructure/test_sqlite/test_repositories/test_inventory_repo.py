import pytest
from cafe_manager.infrastructure.sqlite.repositories.inventory_repo import SQLiteInventoryRepo
from cafe_manager.domain.entities.menu import Ingredient, Unit

class TestSQLiteInventoryRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test_inventory.db"
        return SQLiteInventoryRepo(db_path)

    @pytest.fixture
    def sample_ingredients(self):
        return {
            Ingredient("Coffee Beans", Unit.GRAM): 1000.0,
            Ingredient("Milk", Unit.MILLILITER): 5000.0
        }

    def test_init_db(self, repo):
        with repo._get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
            assert cursor.fetchone() is not None

    def test_save_many_and_get_all(self, repo, sample_ingredients):
        repo.save_many(sample_ingredients)
        retrieved = repo.get_all()
        
        assert len(retrieved) == 2
        for ing, amount in sample_ingredients.items():
            assert retrieved[ing] == amount

    def test_get_by_names(self, repo, sample_ingredients):
        repo.save_many(sample_ingredients)
        retrieved = repo.get_by_names({"Milk"})
        
        assert len(retrieved) == 1
        names = [ing.name for ing in retrieved.keys()]
        assert "Milk" in names
        assert "Coffee Beans" not in names

    def test_save_many_updates_existing(self, repo):
        ing = Ingredient("Sugar", Unit.GRAM)
        repo.save_many({ing: 100.0})
        repo.save_many({ing: 250.0})
        
        retrieved = repo.get_all()
        assert retrieved[ing] == 250.0

    def test_delete_by_name(self, repo, sample_ingredients):
        repo.save_many(sample_ingredients)
        repo.delete_by_name("Milk")
        
        retrieved = repo.get_all()
        assert len(retrieved) == 1
        assert "Milk" not in [ing.name for ing in retrieved.keys()]

    def test_add_ingredient_by_name(self, repo):
        ing = Ingredient("Water", Unit.MILLILITER)
        repo.save_many({ing: 100.0})
        repo.add_ingredient_by_name("Water", 50.5)
        
        retrieved = repo.get_all()
        assert retrieved[ing] == 150.5

    def test_get_free_by_name(self, repo):
        ing = Ingredient("Vanilla", Unit.GRAM)
        repo.save_many({ing: 100.0})
        
        repo.reserve({ing: 30})
            
        free = repo.get_free_by_name("Vanilla")
        assert free == 70.0

    def test_get_free_by_name_not_found(self, repo):
        assert repo.get_free_by_name("Ghost") is None

    def test_reserve(self, repo):
        ing = Ingredient("Tea", Unit.GRAM)
        repo.save_many({ing: 100.0})
        repo.reserve({ing: 25.0})
        
        with repo._get_connection() as conn:
            row = conn.execute("SELECT amount, reserved FROM inventory WHERE name = 'Tea'").fetchone()
            assert row["amount"] == 100.0
            assert row["reserved"] == 25.0

    def test_withdraw(self, repo):
        ing = Ingredient("Beans", Unit.GRAM)
        repo.save_many({ing: 100.0})
        repo.reserve({ing: 40.0})
        
        repo.withdraw({ing: 30.0})
        
        with repo._get_connection() as conn:
            row = conn.execute("SELECT amount, reserved FROM inventory WHERE name = 'Beans'").fetchone()
            assert row["amount"] == 70.0
            assert row["reserved"] == 10.0

    def test_get_all_empty(self, repo):
        assert repo.get_all() is None

    def test_get_by_names_empty(self, repo):
        assert repo.get_by_names({"Milk"}) is None