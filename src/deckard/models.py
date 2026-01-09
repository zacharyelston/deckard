from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationIssue:
    level: str
    message: str
    path: Path | None = None
    location: str | None = None


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def extend(self, issues: list[ValidationIssue]) -> None:
        self.issues.extend(issues)


@dataclass
class ExperimentContext:
    path: Path
    data: dict[str, Any]
