import yaml
from typing import Dict, List, Tuple, Optional, Any


class ValidationError:
    def __init__(self, field: str, message: str, line: Optional[int] = None):
        self.field = field
        self.message = message
        self.line = line
    
    def to_dict(self):
        return {
            'field': self.field,
            'message': self.message,
            'line': self.line
        }


class YAMLValidator:
    MAX_FILE_SIZE = 256 * 1024
    
    def safe_load(self, content: str) -> Tuple[Optional[Dict], Optional[str]]:
        if len(content.encode('utf-8')) > self.MAX_FILE_SIZE:
            return None, f"File exceeds maximum size of {self.MAX_FILE_SIZE // 1024}KB"
        
        try:
            data = yaml.safe_load(content)
            return data, None
        except yaml.YAMLError as e:
            return None, f"YAML parsing error: {str(e)}"
    
    def validate_experiment(self, data: Dict) -> List[ValidationError]:
        errors = []
        
        required_fields = ['version', 'name']
        for field in required_fields:
            if field not in data:
                errors.append(ValidationError(field, f"Required field '{field}' is missing"))
        
        if 'refs' not in data:
            errors.append(ValidationError('refs', "Required section 'refs' is missing"))
        else:
            refs = data['refs']
            if 'deck' not in refs:
                errors.append(ValidationError('refs.deck', "Required field 'refs.deck' is missing"))
            if 'policy' not in refs:
                errors.append(ValidationError('refs.policy', "Required field 'refs.policy' is missing"))
        
        if 'run' not in data:
            errors.append(ValidationError('run', "Required section 'run' is missing"))
        else:
            run = data['run']
            if 'games' not in run:
                errors.append(ValidationError('run.games', "Required field 'run.games' is missing"))
            elif not isinstance(run['games'], int):
                errors.append(ValidationError('run.games', "Field 'run.games' must be an integer"))
            elif run['games'] < 1 or run['games'] > 10:
                errors.append(ValidationError('run.games', "Field 'run.games' must be between 1 and 10 for MVP"))
        
        return errors
    
    def validate_deck(self, data: Dict) -> List[ValidationError]:
        errors = []
        
        required_fields = ['version', 'name', 'mainboard']
        for field in required_fields:
            if field not in data:
                errors.append(ValidationError(field, f"Required field '{field}' is missing"))
        
        if 'mainboard' in data:
            mainboard = data['mainboard']
            if not isinstance(mainboard, (list, dict)):
                errors.append(ValidationError('mainboard', "Field 'mainboard' must be a list or dict"))
            else:
                total_cards = 0
                if isinstance(mainboard, list):
                    for i, entry in enumerate(mainboard):
                        if isinstance(entry, dict):
                            qty = entry.get('qty', entry.get('quantity', 1))
                            if not isinstance(qty, int) or qty < 1:
                                errors.append(ValidationError(f'mainboard[{i}].qty', "Quantity must be a positive integer"))
                            else:
                                total_cards += qty
                        elif isinstance(entry, str):
                            total_cards += 1
                elif isinstance(mainboard, dict):
                    for card, qty in mainboard.items():
                        if not isinstance(qty, int) or qty < 1:
                            errors.append(ValidationError(f'mainboard.{card}', f"Quantity for '{card}' must be a positive integer"))
                        else:
                            total_cards += qty
                
                format_val = data.get('format', 'constructed')
                min_cards = 40 if format_val == 'limited' else 60
                if total_cards < min_cards and total_cards > 0:
                    errors.append(ValidationError('mainboard', f"Deck must have at least {min_cards} cards (found {total_cards})"))
        
        return errors
    
    def validate_policy(self, data: Dict) -> List[ValidationError]:
        errors = []
        
        required_fields = ['version', 'name', 'agent', 'analytics']
        for field in required_fields:
            if field not in data:
                errors.append(ValidationError(field, f"Required field '{field}' is missing"))
        
        if 'agent' in data:
            agent = data['agent']
            if not isinstance(agent, dict):
                errors.append(ValidationError('agent', "Field 'agent' must be an object"))
        
        if 'analytics' in data:
            analytics = data['analytics']
            if not isinstance(analytics, dict):
                errors.append(ValidationError('analytics', "Field 'analytics' must be an object"))
            else:
                if 'outputs' in analytics and not isinstance(analytics['outputs'], (list, dict)):
                    errors.append(ValidationError('analytics.outputs', "Field 'analytics.outputs' must be a list or object"))
        
        return errors
    
    def resolve_reference(self, ref: str, workspace_root: str, current_path: str) -> Tuple[str, bool]:
        if ref.startswith('builtin://'):
            return ref, True
        
        if ref.startswith('repo://'):
            path = ref.replace('repo://', '')
            if workspace_root:
                full_path = f"{workspace_root}/{path}".lstrip('/')
            else:
                full_path = path
            return full_path, True
        
        if ref.startswith('../') or ref.startswith('./'):
            import posixpath
            current_dir = posixpath.dirname(current_path)
            resolved = posixpath.normpath(posixpath.join(current_dir, ref))
            
            if workspace_root:
                ws_root = workspace_root.rstrip('/')
                if not resolved.startswith(ws_root) and not resolved.startswith(ws_root.lstrip('/')):
                    return resolved, False
            return resolved, True
        
        return ref, True


validator = YAMLValidator()
