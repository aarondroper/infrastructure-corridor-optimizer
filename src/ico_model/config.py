"""Shared loading for the versioned analytical model configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when the model configuration is not a JSON object."""


def load_config(path: Path) -> dict[str, Any]:
    """Load the model configuration without changing its project-defined shape."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigError("model configuration must be a JSON object")
    return payload
