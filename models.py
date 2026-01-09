from datetime import datetime
import hashlib
import json

from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    workspaces = db.relationship('Workspace', back_populates='user', lazy='dynamic')
    simulation_runs = db.relationship('SimulationRun', back_populates='user', lazy='dynamic')


class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)


class Workspace(db.Model):
    __tablename__ = 'workspaces'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    repo_url = db.Column(db.String, nullable=False)
    workspace_root = db.Column(db.String, nullable=False, default="")
    commit_sha = db.Column(db.String, nullable=True)
    branch = db.Column(db.String, default="main")
    
    name = db.Column(db.String, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', back_populates='workspaces')
    experiments = db.relationship('Experiment', back_populates='workspace', lazy='dynamic', cascade='all, delete-orphan')
    simulation_runs = db.relationship('SimulationRun', back_populates='workspace', lazy='dynamic')


class Experiment(db.Model):
    __tablename__ = 'experiments'
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    
    path = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=True)
    
    is_valid = db.Column(db.Boolean, default=False)
    validation_errors = db.Column(db.Text, nullable=True)
    
    deck_ref = db.Column(db.String, nullable=True)
    policy_ref = db.Column(db.String, nullable=True)
    games_count = db.Column(db.Integer, default=1)
    
    raw_yaml = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    workspace = db.relationship('Workspace', back_populates='experiments')
    simulation_runs = db.relationship('SimulationRun', back_populates='experiment', lazy='dynamic')


class SimulationRun(db.Model):
    __tablename__ = 'simulation_runs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiments.id'), nullable=False)
    
    status = db.Column(db.String, default='pending')
    seed = db.Column(db.Integer, nullable=True)
    games_requested = db.Column(db.Integer, default=1)
    games_completed = db.Column(db.Integer, default=0)
    
    commit_sha = db.Column(db.String, nullable=True)
    input_hashes = db.Column(db.Text, nullable=True)
    
    results_yaml = db.Column(db.Text, nullable=True)
    report_md = db.Column(db.Text, nullable=True)
    analytics_json = db.Column(db.Text, nullable=True)
    
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', back_populates='simulation_runs')
    workspace = db.relationship('Workspace', back_populates='simulation_runs')
    experiment = db.relationship('Experiment', back_populates='simulation_runs')

    def compute_file_hash(self, content):
        return hashlib.sha256(content.encode()).hexdigest()[:16]
