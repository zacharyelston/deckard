from __future__ import annotations

from pathlib import Path
from typing import Any

from deckard.loader import load_yaml
from deckard.models import ExperimentContext, ValidationIssue, ValidationResult

REQUIRED_EXPERIMENT_FIELDS = ("version", "name", "refs", "run")
REQUIRED_DECK_FIELDS = ("version", "name", "mainboard")
REQUIRED_POLICY_FIELDS = ("version", "name", "agent", "analytics")


class ReferenceResolutionError(ValueError):
    pass


def resolve_reference(workspace_root: Path, ref: str, source_path: Path) -> Path:
    if ref.startswith("builtin://"):
        raise ReferenceResolutionError("builtin:// references are not yet supported")
    if ref.startswith("repo://"):
        rel = ref.removeprefix("repo://")
        candidate = workspace_root / rel
    else:
        candidate = (source_path.parent / ref).resolve()
    try:
        candidate.relative_to(workspace_root.resolve())
    except ValueError as exc:
        raise ReferenceResolutionError("Reference escapes workspace_root") from exc
    return candidate


def validate_required_fields(data: dict[str, Any], required: tuple[str, ...], path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in required:
        if field not in data:
            issues.append(
                ValidationIssue(
                    level="error",
                    message=f"Missing required field '{field}'",
                    path=path,
                )
            )
    return issues


def validate_experiment(context: ExperimentContext, workspace_root: Path) -> ValidationResult:
    result = ValidationResult()
    data = context.data
    result.extend(validate_required_fields(data, REQUIRED_EXPERIMENT_FIELDS, context.path))

    refs = data.get("refs", {})
    if isinstance(refs, dict):
        deck_ref = refs.get("deck")
        policy_ref = refs.get("policy")
        if deck_ref:
            result.extend(validate_deck_reference(deck_ref, context.path, workspace_root))
        else:
            result.add(
                ValidationIssue(
                    level="error",
                    message="refs.deck is required",
                    path=context.path,
                )
            )
        if policy_ref:
            result.extend(validate_policy_reference(policy_ref, context.path, workspace_root))
        else:
            result.add(
                ValidationIssue(
                    level="error",
                    message="refs.policy is required",
                    path=context.path,
                )
            )
    else:
        result.add(
            ValidationIssue(
                level="error",
                message="refs must be a mapping",
                path=context.path,
            )
        )

    run = data.get("run", {})
    if isinstance(run, dict):
        games = run.get("games")
        if games is None:
            result.add(
                ValidationIssue(
                    level="error",
                    message="run.games is required",
                    path=context.path,
                )
            )
        elif not isinstance(games, int) or not 1 <= games <= 10:
            result.add(
                ValidationIssue(
                    level="error",
                    message="run.games must be an integer between 1 and 10",
                    path=context.path,
                )
            )
    else:
        result.add(
            ValidationIssue(
                level="error",
                message="run must be a mapping",
                path=context.path,
            )
        )
    return result


def validate_deck_reference(ref: str, source_path: Path, workspace_root: Path) -> list[ValidationIssue]:
    try:
        path = resolve_reference(workspace_root, ref, source_path)
    except ReferenceResolutionError as exc:
        return [
            ValidationIssue(
                level="error",
                message=f"Deck reference invalid: {exc}",
                path=source_path,
            )
        ]
    if not path.exists():
        return [
            ValidationIssue(
                level="error",
                message=f"Deck reference not found: {path}",
                path=source_path,
            )
        ]
    return validate_deck_file(path)


def validate_policy_reference(ref: str, source_path: Path, workspace_root: Path) -> list[ValidationIssue]:
    try:
        path = resolve_reference(workspace_root, ref, source_path)
    except ReferenceResolutionError as exc:
        return [
            ValidationIssue(
                level="error",
                message=f"Policy reference invalid: {exc}",
                path=source_path,
            )
        ]
    if not path.exists():
        return [
            ValidationIssue(
                level="error",
                message=f"Policy reference not found: {path}",
                path=source_path,
            )
        ]
    return validate_policy_file(path)


def validate_deck_file(path: Path) -> list[ValidationIssue]:
    data = load_yaml(path)
    issues = validate_required_fields(data, REQUIRED_DECK_FIELDS, path)
    mainboard = data.get("mainboard")
    if isinstance(mainboard, list):
        total_cards = sum(
            entry.get("qty", 0)
            for entry in mainboard
            if isinstance(entry, dict)
        )
        if total_cards and total_cards < 60:
            issues.append(
                ValidationIssue(
                    level="error",
                    message="Deck mainboard has fewer than 60 cards",
                    path=path,
                )
            )
    else:
        issues.append(
            ValidationIssue(
                level="error",
                message="mainboard must be a list",
                path=path,
            )
        )
    return issues


def validate_policy_file(path: Path) -> list[ValidationIssue]:
    data = load_yaml(path)
    issues = validate_required_fields(data, REQUIRED_POLICY_FIELDS, path)
    analytics = data.get("analytics")
    if not isinstance(analytics, dict):
        issues.append(
            ValidationIssue(
                level="error",
                message="analytics must be a mapping",
                path=path,
            )
        )
    return issues
