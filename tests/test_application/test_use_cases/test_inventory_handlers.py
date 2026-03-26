import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from decimal import Decimal

from cafe_manager.application.use_cases.inventory_handlers import (
    InventoryAddHandler,
    InventoryRemoveHandler,
    InventoryInfoHandler,
    InventorySupplyHandler,
)
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    IngredientExistsError,
    IngredientNotFoundError,
)
from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.domain.entities.menu import Ingredient, Unit
from cafe_manager.application.interfaces import FinanceRepo, InventoryRepo


class TestInventoryAddHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=InventoryRepo)

    def test_handle_success(self, mock_repo):
        mock_repo.get_by_names.return_value = None
        handler = InventoryAddHandler(mock_repo)

        handler.handle("Coffee", Unit.GRAM, overwrite=False)

        mock_repo.get_by_names.assert_called_once_with({"Coffee"})
        mock_repo.save_many.assert_called_once()
        saved_data = mock_repo.save_many.call_args[0][0]
        assert list(saved_data.keys())[0].name == "Coffee"
        assert list(saved_data.values())[0] == 0

    def test_handle_already_exists_error(self, mock_repo):
        mock_repo.get_by_names.return_value = {MagicMock(): 10.0}
        handler = InventoryAddHandler(mock_repo)

        with pytest.raises(IngredientExistsError):
            handler.handle("Coffee", Unit.GRAM, overwrite=False)

    def test_handle_overwrite_success(self, mock_repo):
        mock_repo.get_by_names.return_value = {MagicMock(): 10.0}
        handler = InventoryAddHandler(mock_repo)

        handler.handle("Coffee", Unit.GRAM, overwrite=True)

        mock_repo.save_many.assert_called_once()


class TestInventoryRemoveHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=InventoryRepo)

    def test_handle_success(self, mock_repo):
        mock_repo.get_by_names.return_value = {MagicMock(): 5.0}
        handler = InventoryRemoveHandler(mock_repo)

        handler.handle("Milk")

        mock_repo.delete_by_name.assert_called_once_with("Milk")

    def test_handle_not_found_error(self, mock_repo):
        mock_repo.get_by_names.return_value = None
        handler = InventoryRemoveHandler(mock_repo)

        with pytest.raises(IngredientNotFoundError):
            handler.handle("Milk")


class TestInventoryInfoHandler:
    def test_handle_returns_inventory(self):
        mock_repo = MagicMock(spec=InventoryRepo)
        inventory = {Ingredient("Tea", Unit.GRAM): 100.0}
        mock_repo.get_all.return_value = inventory

        handler = InventoryInfoHandler(mock_repo)
        result = handler.handle()

        assert result == inventory

    def test_handle_returns_empty_dict_on_none(self):
        mock_repo = MagicMock(spec=InventoryRepo)
        mock_repo.get_all.return_value = None

        handler = InventoryInfoHandler(mock_repo)
        assert handler.handle() == {}


class TestInventorySupplyHandler:
    @pytest.fixture
    def mock_deps(self):
        return MagicMock(spec=InventoryRepo), MagicMock(spec=FinanceRepo)

    def test_handle_success_primary_account(self, mock_deps):
        inv_repo, fin_repo = mock_deps
        account = Account(balance=Money(Decimal("100.00")))
        inv_repo.get_by_names.return_value = {MagicMock(): 0}
        fin_repo.get_primary.return_value = account

        handler = InventorySupplyHandler(inv_repo, fin_repo)
        price = Money(Decimal("20.00"))
        handler.handle("Sugar", 5.0, price, None)

        assert account.balance == Money(Decimal("80.00"))
        fin_repo.save.assert_called_once_with(account)
        inv_repo.add_ingredient_by_name.assert_called_once_with("Sugar", 5.0)

    def test_handle_success_specific_account(self, mock_deps):
        inv_repo, fin_repo = mock_deps
        acc_id = uuid4()
        account = Account(account_id=acc_id, balance=Money(Decimal("50.00")))
        inv_repo.get_by_names.return_value = {MagicMock(): 0}
        fin_repo.get_by_id.return_value = account

        handler = InventorySupplyHandler(inv_repo, fin_repo)
        handler.handle("Sugar", 1.0, Money(Decimal("5.00")), acc_id)

        fin_repo.get_by_id.assert_called_once_with(acc_id)
        assert account.balance == Money(Decimal("45.00"))

    def test_handle_ingredient_not_found(self, mock_deps):
        inv_repo, fin_repo = mock_deps
        inv_repo.get_by_names.return_value = None

        handler = InventorySupplyHandler(inv_repo, fin_repo)
        with pytest.raises(IngredientNotFoundError):
            handler.handle("Unknown", 10, Money.from_any(10), None)

    def test_handle_account_not_found(self, mock_deps):
        inv_repo, fin_repo = mock_deps
        inv_repo.get_by_names.return_value = {MagicMock(): 0}
        fin_repo.get_primary.return_value = None

        handler = InventorySupplyHandler(inv_repo, fin_repo)
        with pytest.raises(AccountNotFoundError):
            handler.handle("Sugar", 1, Money.from_any(1), None)
