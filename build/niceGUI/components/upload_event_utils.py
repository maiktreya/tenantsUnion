"""Helpers for dealing with NiceGUI upload events across versions."""

import inspect
from typing import Any

__all__ = ["read_upload_event_bytes"]


async def read_upload_event_bytes(event: Any) -> bytes:
    """Return raw bytes from an upload event, handling API changes gracefully."""
    for attr in ("file", "content"):
        candidate = getattr(event, attr, None)
        if candidate is None:
            continue

        # prefer an explicit read() method when available
        read = getattr(candidate, "read", None)
        if callable(read):
            data = read()
            if inspect.isawaitable(data):
                data = await data
            try:
                return _ensure_bytes(data)
            except TypeError:
                pass  # fall back to raw candidate handling below

        try:
            return _ensure_bytes(candidate)
        except TypeError:
            continue

    raise AttributeError(
        "Upload event does not expose file bytes via 'file' or 'content' attributes."
    )


def _ensure_bytes(data: Any) -> bytes:
    """Coerce different payload types into bytes for downstream processing."""
    if data is None:
        return b""
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)
    if isinstance(data, str):
        return data.encode("utf-8")
    raise TypeError(f"Unable to coerce {type(data)!r} to bytes")
