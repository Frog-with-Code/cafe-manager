```mermaid
---
config:
  layout: elk
---

classDiagram
direction LR

class ClientRepo {
<<Interface>>
}

class IDGeneratingService {

}

class ClientCreateHandler {
    #_client_repo: ClientRepo
    #_id_generator: IDGeneratingService
    +handle(name: str) str
}

class ClientInfoHandler {
    #_client_repo: ClientRepo
    +handle(client_id: str) Client
}

class ClientListHandler {
    #_client_repo: ClientRepo
    +handle(name: str) list~Client~
}

ClientCreateHandler --> ClientRepo
ClientCreateHandler --> IDGeneratingService
ClientInfoHandler --> ClientRepo
ClientListHandler --> ClientRepo
```