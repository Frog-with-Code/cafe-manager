import httpx
from typing import Any

API = "http://localhost:8000"


async def api_get(path: str, params: dict | None = None) -> tuple[Any, str | None]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{API}{path}", params=params, timeout=5)
            r.raise_for_status()
            return r.json(), None
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = f"HTTP {e.response.status_code}: {e.response.text or str(e)}"
            return None, detail
        except Exception as e:
            return None, str(e)


async def api_post(
    path: str, params: dict | None = None, json: dict | None = None
) -> tuple[Any, str | None]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{API}{path}", params=params, json=json, timeout=5)
            r.raise_for_status()
            return r.json(), None
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = f"HTTP {e.response.status_code}: {e.response.text or str(e)}"
            return None, detail
        except Exception as e:
            return None, str(e)


async def api_delete(path: str, params: dict | None = None) -> tuple[Any, str | None]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.delete(f"{API}{path}", params=params, timeout=5)
            r.raise_for_status()
            return r.json(), None
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = f"HTTP {e.response.status_code}: {e.response.text or str(e)}"
            return None, detail
        except Exception as e:
            return None, str(e)

