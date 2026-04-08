"""Utilities to remove generated runtime artifacts and reset LoGraph state."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def _collect_generated_files(project_root: Path, model_path: Path) -> List[Path]:
    models_dir = project_root / "models"
    generated: List[Path] = []

    # Primary output model path passed by caller.
    generated.append(model_path)

    # Known runtime artifacts created by actions and setup/test runs.
    generated.extend(
        [
            models_dir / "incident_events.jsonl",
            models_dir / "failure_events.jsonl",
            models_dir / "link_predictor_baseline.json",
            models_dir / "lograph_tool_model.lookback.json",
            models_dir / "lograph_tool_model.test.json",
            models_dir / "tmp-auto-setup-model.json",
        ]
    )

    # Remove additional generated model variants.
    for p in models_dir.glob("lograph_tool_model*.json"):
        generated.append(p)

    unique: List[Path] = []
    seen = set()
    for p in generated:
        key = str(p.resolve()) if p.is_absolute() else str((project_root / p).resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def reset_generated_data(project_root: Path, model_path: Path) -> Dict[str, object]:
    """Delete generated runtime files and return a summary report."""
    files = _collect_generated_files(project_root, model_path)
    deleted: List[str] = []
    missing: List[str] = []
    errors: List[str] = []

    for file_path in files:
        target = file_path if file_path.is_absolute() else (project_root / file_path)
        if not target.exists():
            missing.append(str(target))
            continue
        try:
            target.unlink()
            deleted.append(str(target))
        except OSError as exc:
            errors.append(f"{target}: {exc}")

    return {
        "deleted": deleted,
        "missing": missing,
        "errors": errors,
        "deleted_count": len(deleted),
    }
