# MTG Deck Tester

A web application for running Magic: The Gathering deck simulations using files stored in public GitHub repositories.

## Overview

This application allows users to:
- Connect public GitHub repositories containing deck and policy YAML files
- Discover and validate experiments within the repository structure
- Run simulations (1-10 games per experiment)
- View analytics reports and download results

## Project Architecture

### Backend (Flask/Python)
- `app.py` - Flask application setup with SQLAlchemy and database configuration
- `main.py` - Application entry point
- `routes.py` - All HTTP routes and request handlers
- `models.py` - SQLAlchemy database models (User, Workspace, Experiment, SimulationRun)
- `replit_auth.py` - Replit OAuth authentication integration
- `github_service.py` - GitHub API integration for fetching public repos
- `validation_service.py` - YAML validation for experiments, decks, and policies
- `simulation_service.py` - MTG simulation engine (mtg-lite-v0)

### Frontend (Flask Templates)
- `templates/base.html` - Base template with navigation and styling
- `templates/landing.html` - Landing page for unauthenticated users
- `templates/dashboard.html` - User dashboard showing workspaces
- `templates/workspace.html` - Workspace detail view with experiments
- `templates/experiment.html` - Experiment detail and run view
- `templates/run.html` - Simulation results and analytics
- `templates/new_workspace.html` - Form to connect a new repository
- `templates/403.html` - Authentication error page

### Database Schema
- **users** - User accounts (via Replit Auth)
- **oauth** - OAuth tokens for authentication
- **workspaces** - Connected GitHub repositories
- **experiments** - Discovered experiments within workspaces
- **simulation_runs** - Results from simulation runs

## Repository Structure for Experiments

Users should structure their GitHub repositories as follows:

```
workspace_root/
├── experiments/
│   └── exp-name/
│       └── experiment.yaml
├── decks/
│   └── deckname.yaml
└── policies/
    └── policyname.yaml
```

## Development

The application runs on port 5000 with Flask's development server.

### Key Dependencies
- Flask + Flask-SQLAlchemy for web framework
- Flask-Dance + Flask-Login for authentication
- PostgreSQL for database
- PyYAML for YAML parsing
- Requests for GitHub API

## Deployment

Uses Gunicorn for production deployment with autoscaling.

## Recent Changes

- 2026-01-09: Initial implementation
  - Set up Flask application with Replit Auth
  - Created database models for workspaces and experiments
  - Implemented GitHub public repo fetching
  - Added YAML validation for experiments/decks/policies
  - Created simulation service with basic MTG mechanics
  - Built responsive UI with Bootstrap

## User Preferences

(None recorded yet)
