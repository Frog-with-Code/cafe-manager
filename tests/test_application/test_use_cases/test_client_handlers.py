import pytest
from unittest.mock import MagicMock
from cafe_manager.application.use_cases.client_handlers import (
    ClientCreateHandler,
    ClientInfoHandler,
)
from cafe_manager.common.exceptions import ClientNotFoundError
from cafe_manager.domain.entities.people import Client
from cafe_manager.infrastructure.services.id_generator import IDGeneratingService
from cafe_manager.application.uow import ClientRepo


class TestClientCreateHandler:
    @pytest.fixture
    def mock_deps(self):
        client_repo = MagicMock(spec=ClientRepo)
        id_generator = MagicMock(spec=IDGeneratingService)
        id_generator.max_attempts = 100

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.client_repo = client_repo

        return uow, client_repo, id_generator

    def test_handle_success(self, mock_deps):
        uow, client_repo, id_generator = mock_deps
        generated_id = "cli-UNIQUE"
        
        id_generator.generate_unique_code.return_value = generated_id
        client_repo.get_by_id.return_value = None  # No collision
        
        handler = ClientCreateHandler(uow, id_generator)
        result_id = handler.handle("John Doe")
        
        assert result_id == generated_id
        client_repo.save.assert_called_once()
        saved_client = client_repo.save.call_args[0][0]
        assert isinstance(saved_client, Client)
        assert saved_client.name == "John Doe"
        assert saved_client.client_id == generated_id

    def test_handle_with_collision_retry(self, mock_deps):
        uow, client_repo, id_generator = mock_deps
        
        # First ID exists, second is unique
        id_generator.generate_unique_code.side_effect = ["cli-EXIST", "cli-NEW"]
        client_repo.get_by_id.side_effect = [MagicMock(spec=Client), None]
        
        handler = ClientCreateHandler(uow, id_generator)
        result_id = handler.handle("Jane Doe")
        
        assert result_id == "cli-NEW"
        assert id_generator.generate_unique_code.call_count == 2
        assert client_repo.save.call_count == 1


class TestClientInfoHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=ClientRepo)

    def test_handle_success(self, mock_repo):
        client_id = "cli-123"
        expected_client = Client(client_id, "Bob")
        mock_repo.get_by_id.return_value = expected_client

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.client_repo = mock_repo

        handler = ClientInfoHandler(uow)
        result = handler.handle(client_id)
        
        assert result == expected_client
        mock_repo.get_by_id.assert_called_once_with(client_id)

    def test_handle_not_found(self, mock_repo):
        mock_repo.get_by_id.return_value = None

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.client_repo = mock_repo

        handler = ClientInfoHandler(uow)
        with pytest.raises(ClientNotFoundError):
            handler.handle("non-existent-id")