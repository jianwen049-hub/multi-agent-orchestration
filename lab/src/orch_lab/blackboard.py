"""Shared structured state for agents."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Blackboard:
    _data: dict[str, Any] = field(default_factory=dict)
    _meta: dict[str, str] = field(default_factory=dict)

    def set(self, key: str, value: Any, updated_by: str) -> None:
        self._data[key] = value
        self._meta[key] = updated_by

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def snapshot(self) -> dict[str, Any]:
        return {
            "data": copy.deepcopy(self._data),
            "meta": dict(self._meta),
        }
