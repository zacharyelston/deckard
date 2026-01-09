from __future__ import annotations

import argparse
from pathlib import Path

from deckard.validation import validate_experiment
from deckard.workspace import load_experiments


def _cmd_workspace_validate(args: argparse.Namespace) -> int:
    workspace_root = Path(args.root).resolve()
    experiments = load_experiments(workspace_root)
    if not experiments:
        print(f"No experiments found under {workspace_root}")
        return 1

    exit_code = 0
    for context in experiments:
        result = validate_experiment(context, workspace_root)
        status = "ok" if result.is_valid else "error"
        print(f"{context.path}: {status}")
        for issue in result.issues:
            location = f" ({issue.location})" if issue.location else ""
            print(f"  - [{issue.level}] {issue.message}{location}")
        if not result.is_valid:
            exit_code = 2
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deckard workspace utilities")
    subparsers = parser.add_subparsers(dest="command")

    workspace_parser = subparsers.add_parser("workspace", help="Workspace commands")
    workspace_subparsers = workspace_parser.add_subparsers(dest="workspace_command")

    validate_parser = workspace_subparsers.add_parser(
        "validate", help="Validate experiments under a workspace"
    )
    validate_parser.add_argument("--root", required=True, help="Workspace root directory")
    validate_parser.set_defaults(func=_cmd_workspace_validate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
