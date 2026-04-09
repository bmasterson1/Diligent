"""Config file reader/writer for config.json."""

import json
from pathlib import Path

from diligent.state.models import ConfigFile


def read_config(path: Path) -> ConfigFile:
    """Read config.json into a ConfigFile dataclass."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ConfigFile(
        schema_version=data["schema_version"],
        deal_code=data["deal_code"],
        created=data["created"],
        anchor_tolerance_pct=data["anchor_tolerance_pct"],
        recent_window_days=data["recent_window_days"],
        workstreams=data.get("workstreams", []),
    )


def write_config(path: Path, config: ConfigFile) -> None:
    """Write a ConfigFile to config.json using atomic_write."""
    from diligent.helpers.io import atomic_write

    data = {
        "schema_version": config.schema_version,
        "deal_code": config.deal_code,
        "created": config.created,
        "anchor_tolerance_pct": config.anchor_tolerance_pct,
        "recent_window_days": config.recent_window_days,
        "workstreams": config.workstreams,
    }
    content = json.dumps(data, indent=2) + "\n"
    atomic_write(path, content)
