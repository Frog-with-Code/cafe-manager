import httpx
from typing import Any

from nicegui import app

API = "http://localhost:8000"


client = httpx.AsyncClient(base_url=API, timeout=5)


@app.on_shutdown
async def close_client() -> None:
    await client.aclose()


async def api_get(path: str, params: dict | None = None) -> tuple[Any, str | None]:
    try:
        r = await client.get(path, params=params)
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
    try:
        r = await client.post(path, params=params, json=json, timeout=5)
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
    try:
        r = await client.delete(path, params=params, timeout=5)
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
