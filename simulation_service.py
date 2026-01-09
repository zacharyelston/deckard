import random
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class SimulationService:
    def __init__(self):
        self.supported_mechanics = [
            'draw', 'play_land', 'cast_creature', 'cast_spell',
            'attack', 'block', 'damage', 'life_change'
        ]
    
    def run_simulation(
        self,
        experiment: Dict,
        deck: Dict,
        policy: Dict,
        games: int = 1,
        seed: Optional[int] = None
    ) -> Dict:
        if seed is None:
            seed = random.randint(1, 2**31 - 1)
        
        random.seed(seed)
        
        results = {
            'version': '1.0',
            'sim_id': hashlib.sha256(f"{seed}{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            'seed': seed,
            'games_requested': games,
            'games_completed': 0,
            'game_results': [],
            'aggregate_stats': {},
            'started_at': datetime.now().isoformat(),
            'completed_at': None
        }
        
        for game_num in range(1, games + 1):
            game_result = self._simulate_game(game_num, deck, policy)
            results['game_results'].append(game_result)
            results['games_completed'] += 1
        
        results['aggregate_stats'] = self._compute_aggregate_stats(results['game_results'])
        results['completed_at'] = datetime.now().isoformat()
        
        return results
    
    def _simulate_game(self, game_num: int, deck: Dict, policy: Dict) -> Dict:
        player_life = 20
        opponent_life = 20
        turns = 0
        max_turns = 20
        
        hand_size = 7
        lands_played = 0
        creatures_played = 0
        spells_cast = 0
        damage_dealt = 0
        
        game_log = []
        
        game_log.append(f"Game {game_num} started. Drawing {hand_size} cards.")
        
        while turns < max_turns and player_life > 0 and opponent_life > 0:
            turns += 1
            game_log.append(f"Turn {turns}")
            
            if random.random() < 0.4:
                lands_played += 1
                game_log.append("  Played a land")
            
            if lands_played > 0 and random.random() < 0.3:
                creatures_played += 1
                game_log.append("  Cast a creature")
            
            if lands_played >= 2 and random.random() < 0.2:
                spells_cast += 1
                game_log.append("  Cast a spell")
            
            if creatures_played > 0 and random.random() < 0.5:
                attack_damage = random.randint(1, 3) * min(creatures_played, 3)
                opponent_life -= attack_damage
                damage_dealt += attack_damage
                game_log.append(f"  Attacked for {attack_damage} damage (Opponent life: {opponent_life})")
            
            if random.random() < 0.3:
                opp_damage = random.randint(1, 4)
                player_life -= opp_damage
                game_log.append(f"  Opponent dealt {opp_damage} damage (Player life: {player_life})")
        
        won = opponent_life <= 0 and player_life > 0
        draw = player_life <= 0 and opponent_life <= 0
        
        return {
            'game_number': game_num,
            'result': 'win' if won else ('draw' if draw else 'loss'),
            'turns': turns,
            'final_life': player_life,
            'opponent_final_life': opponent_life,
            'stats': {
                'lands_played': lands_played,
                'creatures_played': creatures_played,
                'spells_cast': spells_cast,
                'damage_dealt': damage_dealt
            },
            'log': game_log
        }
    
    def _compute_aggregate_stats(self, game_results: List[Dict]) -> Dict:
        if not game_results:
            return {}
        
        wins = sum(1 for g in game_results if g['result'] == 'win')
        losses = sum(1 for g in game_results if g['result'] == 'loss')
        draws = sum(1 for g in game_results if g['result'] == 'draw')
        total = len(game_results)
        
        avg_turns = sum(g['turns'] for g in game_results) / total
        avg_damage = sum(g['stats']['damage_dealt'] for g in game_results) / total
        avg_lands = sum(g['stats']['lands_played'] for g in game_results) / total
        avg_creatures = sum(g['stats']['creatures_played'] for g in game_results) / total
        
        return {
            'total_games': total,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
            'avg_turns': round(avg_turns, 1),
            'avg_damage_dealt': round(avg_damage, 1),
            'avg_lands_played': round(avg_lands, 1),
            'avg_creatures_played': round(avg_creatures, 1)
        }
    
    def generate_report(self, results: Dict, experiment: Dict, deck: Dict, policy: Dict) -> str:
        stats = results.get('aggregate_stats', {})
        
        report = f"""# Simulation Report

## Experiment: {experiment.get('name', 'Unknown')}

### Summary
- **Games Played**: {stats.get('total_games', 0)}
- **Wins**: {stats.get('wins', 0)}
- **Losses**: {stats.get('losses', 0)}
- **Draws**: {stats.get('draws', 0)}
- **Win Rate**: {stats.get('win_rate', 0)}%

### Performance Metrics
- **Average Turns per Game**: {stats.get('avg_turns', 0)}
- **Average Damage Dealt**: {stats.get('avg_damage_dealt', 0)}
- **Average Lands Played**: {stats.get('avg_lands_played', 0)}
- **Average Creatures Played**: {stats.get('avg_creatures_played', 0)}

### Deck: {deck.get('name', 'Unknown')}
### Policy: {policy.get('name', 'Unknown')}

### Reproducibility
- **Seed**: {results.get('seed')}
- **Simulation ID**: {results.get('sim_id')}
- **Started**: {results.get('started_at')}
- **Completed**: {results.get('completed_at')}

---
*Report generated by MTG Deck Tester (mtg-lite-v0)*
"""
        return report


simulation_service = SimulationService()
