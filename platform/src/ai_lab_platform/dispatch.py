"""HTTP dispatch from the M1 control plane to a Studio worker. Not LangGraph."""

from __future__ import annotations

from typing import Any, Callable, Protocol


class StudioUnavailable(Exception):
    """Studio worker did not accept the job. The work order must remain persisted."""


DispatchFn = Callable[[dict[str, Any]], dict[str, Any]]


class WorkerClient(Protocol):
    def submit(self, payload: dict[str, Any]) -> dict[str, Any]: ...


def http_dispatch(base_url: str, timeout_seconds: float = 2.0) -> DispatchFn:
    """Return a dispatch function. Callers must not treat transport errors as 'job gone'."""
    import httpx

    def _call(payload: dict[str, Any]) -> dict[str, Any]:
        url = base_url.rstrip("/") + "/v1/tasks"
        try:
            response = httpx.post(url, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise StudioUnavailable("worker returned a non-object JSON body")
            return data
        except httpx.HTTPError as exc:
            raise StudioUnavailable(str(exc)) from exc

    return _call
