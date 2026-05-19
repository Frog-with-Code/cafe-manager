from typing import Any, Callable, Coroutine

refreshers: dict[str, Callable[[], Coroutine[Any, Any, None]]] = {}
