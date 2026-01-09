import random
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any


class SimulationService:
    def __init__(self):
        self.supported_mechanics = [
            'draw', 'play_land', 'cast_creature', 'cast_spell',
            'attack', 'block', 'damage', 'life_change'
        ]
    
    def _parse_deck(self, deck: Dict) -> Dict:
        mainboard = deck.get('mainboard', {})
        cards = []
        lands = []
        creatures = []
        spells = []
        
        if isinstance(mainboard, list):
            for entry in mainboard:
                if isinstance(entry, dict):
                    name = entry.get('name', entry.get('card', 'Unknown Card'))
                    qty = entry.get('qty', entry.get('quantity', 1))
                    card_type = entry.get('type', 'spell')
                else:
                    name = str(entry)
                    qty = 1
                    card_type = 'land' if 'land' in name.lower() else 'creature' if 'creature' in name.lower() else 'spell'
                
                for _ in range(qty):
                    card = {'name': name, 'type': card_type}
                    cards.append(card)
                    if card_type == 'land':
                        lands.append(card)
                    elif card_type == 'creature':
                        creatures.append(card)
                    else:
                        spells.append(card)
        
        elif isinstance(mainboard, dict):
            for name, qty in mainboard.items():
                card_type = 'land' if 'land' in name.lower() else 'creature' if any(x in name.lower() for x in ['creature', 'goblin', 'elf', 'dragon', 'knight']) else 'spell'
                for _ in range(int(qty)):
                    card = {'name': name, 'type': card_type}
                    cards.append(card)
                    if card_type == 'land':
                        lands.append(card)
                    elif card_type == 'creature':
                        creatures.append(card)
                    else:
                        spells.append(card)
        
        total_cards = len(cards) or 60
        return {
            'cards': cards,
            'total': total_cards,
            'land_ratio': len(lands) / total_cards if total_cards > 0 else 0.4,
            'creature_ratio': len(creatures) / total_cards if total_cards > 0 else 0.3,
            'spell_ratio': len(spells) / total_cards if total_cards > 0 else 0.3,
            'deck_name': deck.get('name', 'Unknown Deck')
        }
    
    def _parse_policy(self, policy: Dict) -> Dict:
        agent = policy.get('agent', {})
        
        return {
            'aggression': agent.get('aggression', 0.5),
            'risk_tolerance': agent.get('risk_tolerance', 0.5),
            'mulligan_threshold': agent.get('mulligan_threshold', 4),
            'attack_threshold': agent.get('attack_threshold', 0.3),
            'policy_name': policy.get('name', 'Unknown Policy')
        }
    
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
        
        parsed_deck = self._parse_deck(deck)
        parsed_policy = self._parse_policy(policy)
        
        results = {
            'version': '1.0',
            'sim_id': hashlib.sha256(f"{seed}{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            'seed': seed,
            'games_requested': games,
            'games_completed': 0,
            'game_results': [],
            'aggregate_stats': {},
            'deck_info': {
                'name': parsed_deck['deck_name'],
                'total_cards': parsed_deck['total'],
                'land_ratio': round(parsed_deck['land_ratio'], 2),
                'creature_ratio': round(parsed_deck['creature_ratio'], 2)
            },
            'policy_info': {
                'name': parsed_policy['policy_name'],
                'aggression': parsed_policy['aggression']
            },
            'started_at': datetime.now().isoformat(),
            'completed_at': None
        }
        
        for game_num in range(1, games + 1):
            game_result = self._simulate_game(game_num, parsed_deck, parsed_policy)
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
        
        library = list(deck.get('cards', []))
        random.shuffle(library)
        
        land_ratio = deck.get('land_ratio', 0.4)
        creature_ratio = deck.get('creature_ratio', 0.3)
        aggression = policy.get('aggression', 0.5)
        attack_threshold = policy.get('attack_threshold', 0.3)
        
        hand_size = 7
        hand = library[:hand_size] if len(library) >= hand_size else library[:]
        library = library[hand_size:]
        
        lands_in_play = 0
        creatures_in_play = 0
        lands_played = 0
        creatures_played = 0
        spells_cast = 0
        damage_dealt = 0
        cards_drawn = hand_size
        
        game_log = []
        game_log.append(f"Game {game_num} started with deck '{deck.get('deck_name', 'Unknown')}'")
        game_log.append(f"Deck composition: {round(land_ratio*100)}% lands, {round(creature_ratio*100)}% creatures")
        game_log.append(f"Opening hand: {hand_size} cards")
        
        while turns < max_turns and player_life > 0 and opponent_life > 0:
            turns += 1
            game_log.append(f"Turn {turns}")
            
            if library:
                drawn = library.pop(0)
                cards_drawn += 1
                game_log.append(f"  Drew: {drawn.get('name', 'a card')}")
                hand.append(drawn)
            
            land_chance = land_ratio * 0.8 + 0.2
            if random.random() < land_chance and any(c.get('type') == 'land' for c in hand):
                lands_in_play += 1
                lands_played += 1
                for i, c in enumerate(hand):
                    if c.get('type') == 'land':
                        game_log.append(f"  Played land: {c.get('name', 'a land')}")
                        hand.pop(i)
                        break
            
            if lands_in_play > 0:
                creature_chance = creature_ratio * aggression * 1.5
                if random.random() < creature_chance and any(c.get('type') == 'creature' for c in hand):
                    creatures_in_play += 1
                    creatures_played += 1
                    for i, c in enumerate(hand):
                        if c.get('type') == 'creature':
                            game_log.append(f"  Cast creature: {c.get('name', 'a creature')}")
                            hand.pop(i)
                            break
            
            if lands_in_play >= 2:
                spell_chance = (1 - land_ratio - creature_ratio) * 0.5
                if random.random() < spell_chance and any(c.get('type') == 'spell' for c in hand):
                    spells_cast += 1
                    for i, c in enumerate(hand):
                        if c.get('type') == 'spell':
                            game_log.append(f"  Cast spell: {c.get('name', 'a spell')}")
                            hand.pop(i)
                            break
            
            if creatures_in_play > 0 and random.random() < (attack_threshold + aggression * 0.4):
                base_damage = min(creatures_in_play, 4)
                attack_damage = random.randint(1, 2) + base_damage
                attack_damage = int(attack_damage * (1 + aggression * 0.3))
                opponent_life -= attack_damage
                damage_dealt += attack_damage
                game_log.append(f"  Attacked with {creatures_in_play} creature(s) for {attack_damage} damage (Opponent: {opponent_life})")
            
            opp_aggression = 0.5
            if random.random() < (0.2 + opp_aggression * 0.3):
                opp_damage = random.randint(1, 3) + turns // 4
                player_life -= opp_damage
                game_log.append(f"  Opponent dealt {opp_damage} damage (Player: {player_life})")
        
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
                'damage_dealt': damage_dealt,
                'cards_drawn': cards_drawn
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
        avg_cards = sum(g['stats']['cards_drawn'] for g in game_results) / total
        
        return {
            'total_games': total,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
            'avg_turns': round(avg_turns, 1),
            'avg_damage_dealt': round(avg_damage, 1),
            'avg_lands_played': round(avg_lands, 1),
            'avg_creatures_played': round(avg_creatures, 1),
            'avg_cards_drawn': round(avg_cards, 1)
        }
    
    def generate_report(self, results: Dict, experiment: Dict, deck: Dict, policy: Dict) -> str:
        stats = results.get('aggregate_stats', {})
        deck_info = results.get('deck_info', {})
        policy_info = results.get('policy_info', {})
        
        report = f"""# Simulation Report

## Experiment: {experiment.get('name', 'Unknown')}

### Summary
- **Games Played**: {stats.get('total_games', 0)}
- **Wins**: {stats.get('wins', 0)}
- **Losses**: {stats.get('losses', 0)}
- **Draws**: {stats.get('draws', 0)}
- **Win Rate**: {stats.get('win_rate', 0)}%

### Deck Analysis
- **Deck Name**: {deck_info.get('name', deck.get('name', 'Unknown'))}
- **Total Cards**: {deck_info.get('total_cards', 'N/A')}
- **Land Ratio**: {deck_info.get('land_ratio', 'N/A')}
- **Creature Ratio**: {deck_info.get('creature_ratio', 'N/A')}

### Policy Configuration
- **Policy Name**: {policy_info.get('name', policy.get('name', 'Unknown'))}
- **Aggression Level**: {policy_info.get('aggression', 'N/A')}

### Performance Metrics
- **Average Turns per Game**: {stats.get('avg_turns', 0)}
- **Average Damage Dealt**: {stats.get('avg_damage_dealt', 0)}
- **Average Lands Played**: {stats.get('avg_lands_played', 0)}
- **Average Creatures Played**: {stats.get('avg_creatures_played', 0)}
- **Average Cards Drawn**: {stats.get('avg_cards_drawn', 0)}

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
