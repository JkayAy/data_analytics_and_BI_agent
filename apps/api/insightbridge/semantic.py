from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from insightbridge.config import settings


def load_semantic_layer(path: Path | None = None) -> dict[str, Any]:
    p = path or settings.resolved_semantic_layer_path()
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def allowed_schemas(layer: dict[str, Any]) -> set[str]:
    policies = layer.get("policies") or {}
    return set(policies.get("allowed_schemas") or ["analytics"])


def pii_columns(layer: dict[str, Any]) -> set[str]:
    cols: set[str] = set()
    for meta in (layer.get("tables") or {}).values():
        for col_name, col_meta in (meta.get("columns") or {}).items():
            if isinstance(col_meta, dict) and col_meta.get("pii"):
                cols.add(col_name)
    return cols


def semantic_context_for_prompt(layer: dict[str, Any]) -> str:
    lines = [
        f"Semantic layer v{layer.get('version', 1)} — {layer.get('description', '')}",
        "",
        "Tables (PostgreSQL):",
    ]
    for table, meta in (layer.get("tables") or {}).items():
        cols = ", ".join((meta.get("columns") or {}).keys())
        lines.append(f"  - {table}({cols})")

    lines.append("")
    lines.append("Defined metrics (prefer these definitions):")
    for name, m in (layer.get("metrics") or {}).items():
        lines.append(f"  - {name}: {m.get('label')} => {m.get('sql')} FROM {m.get('from')}")

    lines.append("")
    lines.append("Dimensions:")
    for name, d in (layer.get("dimensions") or {}).items():
        lines.append(f"  - {name}: {d.get('column')} on {d.get('table')}")

    lines.append("")
    lines.append("Rules: SELECT only; use schema analytics; always include LIMIT 1000 or less.")
    return "\n".join(lines)
