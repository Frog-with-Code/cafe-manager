from cafe_manager.domain.entities.people import Client
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.application.interfaces import ClientRepo
from cafe_manager.common.exceptions import ClientNotFoundError


class ClientCreateHandler:
    def __init__(
        self, client_repo: ClientRepo, id_generator: IDGeneratingService
    ) -> None:
        self._client_repo = client_repo
        self._id_generator = id_generator

    def handle(self, name: str) -> str:
        for _ in range(self._id_generator.max_attempts):
            generated_id = self._id_generator.generate_unique_code(Client)
            client = self._client_repo.get_by_id(generated_id)

            if client is None:
                break
        else:
            raise RuntimeError("Unique code was not generated. Try to use longer code")

        new_client = Client(generated_id, name)
        self._client_repo.save(new_client)

        return generated_id


class ClientInfoHandler:
    def __init__(self, client_repo: ClientRepo) -> None:
        self._client_repo = client_repo

    def handle(self, client_id: str) -> Client:
        client = self._client_repo.get_by_id(client_id)

        if client is None:
            raise ClientNotFoundError(f"Client with ID {client_id} was not found")

        return client
