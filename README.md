# Deckard

Deckard is the skeleton for the Public GitHub Experiments Runner (MTG Deck Tester).
It focuses on discovering experiments inside a repository workspace, loading YAML
artifacts, and validating references based on the PRD/workspace spec.

## Current Scope

- Workspace discovery for `experiments/*/experiment.yaml`.
- YAML loading with safe parsing.
- Basic validation for experiment, deck, and policy files.
- CLI entry point for listing experiments and validation output.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

deckard workspace validate --root /path/to/workspace
```

## Repo Layout

```
experiments/    # experiment.yaml folders
policies/       # policy YAML definitions
./decks/        # deck YAML definitions
src/deckard/    # app skeleton
```
