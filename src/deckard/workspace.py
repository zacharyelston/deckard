from __future__ import annotations

from pathlib import Path
from typing import Iterable

from deckard.loader import load_yaml
from deckard.models import ExperimentContext

EXPERIMENT_FILENAME = "experiment.yaml"


def discover_experiments(workspace_root: Path) -> list[Path]:
    experiments_root = workspace_root / "experiments"
    if not experiments_root.exists():
        return []
    return sorted(experiments_root.glob(f"*/{EXPERIMENT_FILENAME}"))


def load_experiments(workspace_root: Path) -> list[ExperimentContext]:
    contexts: list[ExperimentContext] = []
    for path in discover_experiments(workspace_root):
        contexts.append(ExperimentContext(path=path, data=load_yaml(path)))
    return contexts


def iter_workspace_files(workspace_root: Path, patterns: Iterable[str]) -> list[Path]:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(sorted(workspace_root.glob(pattern)))
    return matches
