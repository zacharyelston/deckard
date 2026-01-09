import json
import yaml
from flask import session, render_template, request, redirect, url_for, flash, jsonify, Response
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from flask_login import current_user
from models import Workspace, Experiment, SimulationRun
from github_service import github_service
from validation_service import validator
from simulation_service import simulation_service

app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    if current_user.is_authenticated:
        workspaces = Workspace.query.filter_by(user_id=current_user.id).order_by(Workspace.created_at.desc()).all()
        return render_template('dashboard.html', user=current_user, workspaces=workspaces)
    return render_template('landing.html')

@app.route('/workspace/new', methods=['GET', 'POST'])
@require_login
def new_workspace():
    if request.method == 'POST':
        repo_url = request.form.get('repo_url', '').strip()
        workspace_root = request.form.get('workspace_root', '').strip()
        
        owner, repo = github_service.parse_repo_url(repo_url)
        if not owner or not repo:
            flash('Invalid GitHub repository URL', 'error')
            return render_template('new_workspace.html', user=current_user)
        
        is_valid, message = github_service.validate_public_repo(owner, repo)
        if not is_valid:
            flash(message, 'error')
            return render_template('new_workspace.html', user=current_user)
        
        branch = github_service.get_default_branch(owner, repo)
        commit_sha = github_service.get_latest_commit(owner, repo, branch)
        
        workspace = Workspace(
            user_id=current_user.id,
            repo_url=repo_url,
            workspace_root=workspace_root,
            branch=branch,
            commit_sha=commit_sha,
            name=f"{owner}/{repo}"
        )
        db.session.add(workspace)
        db.session.commit()
        
        discover_experiments_for_workspace(workspace, owner, repo)
        
        flash('Workspace connected successfully!', 'success')
        return redirect(url_for('view_workspace', workspace_id=workspace.id))
    
    return render_template('new_workspace.html', user=current_user)

def discover_experiments_for_workspace(workspace, owner, repo):
    experiments = github_service.discover_experiments(
        owner, repo, workspace.workspace_root, workspace.commit_sha or 'HEAD'
    )
    
    for exp_info in experiments:
        content = github_service.get_file_content(
            owner, repo, exp_info['path'], workspace.commit_sha or 'HEAD'
        )
        
        exp = Experiment(
            workspace_id=workspace.id,
            path=exp_info['path'],
            name=exp_info['name']
        )
        
        if content:
            exp.raw_yaml = content
            data, error = validator.safe_load(content)
            
            if error:
                exp.is_valid = False
                exp.validation_errors = json.dumps([{'field': 'yaml', 'message': error}])
            else:
                errors = validator.validate_experiment(data)
                if errors:
                    exp.is_valid = False
                    exp.validation_errors = json.dumps([e.to_dict() for e in errors])
                else:
                    exp.is_valid = True
                    exp.deck_ref = data.get('refs', {}).get('deck')
                    exp.policy_ref = data.get('refs', {}).get('policy')
                    exp.games_count = data.get('run', {}).get('games', 1)
        else:
            exp.is_valid = False
            exp.validation_errors = json.dumps([{'field': 'file', 'message': 'Could not fetch experiment file'}])
        
        db.session.add(exp)
    
    db.session.commit()

@app.route('/workspace/<int:workspace_id>')
@require_login
def view_workspace(workspace_id):
    workspace = Workspace.query.filter_by(id=workspace_id, user_id=current_user.id).first_or_404()
    experiments = workspace.experiments.all()
    runs = workspace.simulation_runs.order_by(SimulationRun.created_at.desc()).limit(10).all()
    return render_template('workspace.html', user=current_user, workspace=workspace, experiments=experiments, runs=runs)

@app.route('/workspace/<int:workspace_id>/refresh', methods=['POST'])
@require_login
def refresh_workspace(workspace_id):
    workspace = Workspace.query.filter_by(id=workspace_id, user_id=current_user.id).first_or_404()
    
    owner, repo = github_service.parse_repo_url(workspace.repo_url)
    if owner and repo:
        commit_sha = github_service.get_latest_commit(owner, repo, workspace.branch)
        workspace.commit_sha = commit_sha
        
        Experiment.query.filter_by(workspace_id=workspace.id).delete()
        db.session.commit()
        
        discover_experiments_for_workspace(workspace, owner, repo)
        
        flash('Workspace refreshed successfully!', 'success')
    
    return redirect(url_for('view_workspace', workspace_id=workspace_id))

@app.route('/workspace/<int:workspace_id>/delete', methods=['POST'])
@require_login
def delete_workspace(workspace_id):
    workspace = Workspace.query.filter_by(id=workspace_id, user_id=current_user.id).first_or_404()
    db.session.delete(workspace)
    db.session.commit()
    flash('Workspace deleted.', 'info')
    return redirect(url_for('index'))

@app.route('/experiment/<int:experiment_id>')
@require_login
def view_experiment(experiment_id):
    experiment = Experiment.query.get_or_404(experiment_id)
    workspace = experiment.workspace
    if workspace.user_id != current_user.id:
        return "Unauthorized", 403
    
    runs = experiment.simulation_runs.order_by(SimulationRun.created_at.desc()).all()
    return render_template('experiment.html', user=current_user, experiment=experiment, workspace=workspace, runs=runs)

@app.route('/experiment/<int:experiment_id>/run', methods=['POST'])
@require_login
def run_experiment(experiment_id):
    experiment = Experiment.query.get_or_404(experiment_id)
    workspace = experiment.workspace
    if workspace.user_id != current_user.id:
        return "Unauthorized", 403
    
    if not experiment.is_valid:
        flash('Cannot run invalid experiment. Please fix validation errors first.', 'error')
        return redirect(url_for('view_experiment', experiment_id=experiment_id))
    
    owner, repo = github_service.parse_repo_url(workspace.repo_url)
    
    exp_data, _ = validator.safe_load(experiment.raw_yaml)
    
    deck_content = None
    policy_content = None
    
    if experiment.deck_ref:
        resolved_deck, valid = validator.resolve_reference(
            experiment.deck_ref, workspace.workspace_root, experiment.path
        )
        if not resolved_deck.startswith('builtin://'):
            deck_content = github_service.get_file_content(owner, repo, resolved_deck, workspace.commit_sha)
    
    if experiment.policy_ref:
        resolved_policy, valid = validator.resolve_reference(
            experiment.policy_ref, workspace.workspace_root, experiment.path
        )
        if not resolved_policy.startswith('builtin://'):
            policy_content = github_service.get_file_content(owner, repo, resolved_policy, workspace.commit_sha)
    
    deck_data = {}
    policy_data = {}
    
    if deck_content:
        deck_data, _ = validator.safe_load(deck_content)
        deck_data = deck_data or {}
    else:
        deck_data = {'name': 'Default Deck', 'mainboard': {}}
    
    if policy_content:
        policy_data, _ = validator.safe_load(policy_content)
        policy_data = policy_data or {}
    else:
        policy_data = {'name': 'Default Policy', 'agent': {}, 'analytics': {}}
    
    games = min(max(experiment.games_count, 1), 10)
    
    results = simulation_service.run_simulation(
        exp_data or {},
        deck_data,
        policy_data,
        games=games
    )
    
    report = simulation_service.generate_report(results, exp_data or {}, deck_data, policy_data)
    
    run = SimulationRun(
        user_id=current_user.id,
        workspace_id=workspace.id,
        experiment_id=experiment.id,
        status='completed',
        seed=results['seed'],
        games_requested=games,
        games_completed=results['games_completed'],
        commit_sha=workspace.commit_sha,
        results_yaml=yaml.dump(results, default_flow_style=False),
        report_md=report,
        analytics_json=json.dumps(results.get('aggregate_stats', {})),
        started_at=results.get('started_at'),
        completed_at=results.get('completed_at')
    )
    db.session.add(run)
    db.session.commit()
    
    flash(f'Simulation completed! {results["games_completed"]} games played.', 'success')
    return redirect(url_for('view_run', run_id=run.id))

@app.route('/run/<int:run_id>')
@require_login
def view_run(run_id):
    run = SimulationRun.query.get_or_404(run_id)
    if run.user_id != current_user.id:
        return "Unauthorized", 403
    
    return render_template('run.html', user=current_user, run=run)

@app.route('/run/<int:run_id>/download/<file_type>')
@require_login
def download_run_file(run_id, file_type):
    run = SimulationRun.query.get_or_404(run_id)
    if run.user_id != current_user.id:
        return "Unauthorized", 403
    
    if file_type == 'results':
        content = run.results_yaml or ''
        filename = f'results_{run.id}.yaml'
        mimetype = 'text/yaml'
    elif file_type == 'report':
        content = run.report_md or ''
        filename = f'report_{run.id}.md'
        mimetype = 'text/markdown'
    else:
        return "Invalid file type", 400
    
    return Response(
        content,
        mimetype=mimetype,
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
