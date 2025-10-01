"""Shared normalization helpers for importer workflows."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, List, Optional, Sequence, TypeVar

T = TypeVar("T")


def normalize_for_sorting(value: Any) -> str:
    """Return a normalized string key for consistent sorting across types."""
    if value is None:
        return ""

    if isinstance(value, bool):
        return "1" if value else "0"

    text = str(value).strip()
    if re.match(r"^-?(?:\d+\.?\d*|\.\d+)$", text):
        try:
            number = float(text)
            return f"{number:020.6f}"
        except (TypeError, ValueError):
            pass

    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def normalize_address_key(address: Optional[str]) -> str:
    """Create an accent-insensitive key suitable for comparing addresses."""
    if not address:
        return ""
    normalized = unicodedata.normalize("NFD", address.strip().lower())
    collapsed = re.sub(r"\s+", " ", normalized)
    return "".join(c for c in collapsed if unicodedata.category(c) != "Mn")


def chunk_list(values: Sequence[T], chunk_size: int = 30) -> List[List[T]]:
    """Return fixed-size chunks from an input sequence."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    return [list(values[i : i + chunk_size]) for i in range(0, len(values), chunk_size)]


def format_in_filter_value(value: str) -> str:
    """Escape a literal for usage inside a PostgREST in() filter."""
    escaped = value.replace('"', '""')
    return f'"{escaped}"'


__all__ = [
    "normalize_for_sorting",
    "normalize_address_key",
    "chunk_list",
    "format_in_filter_value",
]
