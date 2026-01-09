import re
import requests
from typing import Optional, Dict, List, Tuple
import base64


class GitHubService:
    def __init__(self):
        self.api_base = "https://api.github.com"
    
    def parse_repo_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        patterns = [
            r'github\.com[:/]([^/]+)/([^/\.]+)',
            r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).rstrip('.git')
        return None, None
    
    def get_default_branch(self, owner: str, repo: str) -> Optional[str]:
        url = f"{self.api_base}/repos/{owner}/{repo}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('default_branch', 'main')
        except requests.RequestException:
            pass
        return 'main'
    
    def get_latest_commit(self, owner: str, repo: str, branch: str = 'main') -> Optional[str]:
        url = f"{self.api_base}/repos/{owner}/{repo}/commits/{branch}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('sha')
        except requests.RequestException:
            pass
        return None
    
    def get_tree(self, owner: str, repo: str, path: str = "", sha: str = "HEAD") -> List[Dict]:
        url = f"{self.api_base}/repos/{owner}/{repo}/git/trees/{sha}?recursive=1"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                tree = response.json().get('tree', [])
                if path:
                    path = path.rstrip('/') + '/'
                    return [item for item in tree if item['path'].startswith(path)]
                return tree
        except requests.RequestException:
            pass
        return []
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "HEAD") -> Optional[str]:
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('encoding') == 'base64':
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content
                return data.get('content', '')
        except (requests.RequestException, UnicodeDecodeError):
            pass
        return None
    
    def discover_experiments(self, owner: str, repo: str, workspace_root: str, sha: str = "HEAD") -> List[Dict]:
        experiments = []
        tree = self.get_tree(owner, repo, workspace_root, sha)
        
        experiments_path = f"{workspace_root}/experiments/" if workspace_root else "experiments/"
        experiments_path = experiments_path.lstrip('/')
        
        for item in tree:
            if item['type'] == 'blob' and item['path'].endswith('/experiment.yaml'):
                if experiments_path in item['path'] or item['path'].startswith('experiments/'):
                    exp_folder = item['path'].rsplit('/experiment.yaml', 1)[0]
                    exp_name = exp_folder.split('/')[-1]
                    experiments.append({
                        'path': item['path'],
                        'name': exp_name,
                        'folder': exp_folder
                    })
        
        return experiments
    
    def validate_public_repo(self, owner: str, repo: str) -> Tuple[bool, str]:
        url = f"{self.api_base}/repos/{owner}/{repo}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('private', True):
                    return False, "This is a private repository. Only public repos are supported."
                return True, "Repository is valid and public."
            elif response.status_code == 404:
                return False, "Repository not found. Please check the URL."
            else:
                return False, f"Unable to access repository (status: {response.status_code})."
        except requests.RequestException as e:
            return False, f"Error connecting to GitHub: {str(e)}"


github_service = GitHubService()
