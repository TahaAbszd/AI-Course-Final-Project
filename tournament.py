import csv
from datetime import datetime
from typing import List, Dict, Optional
from game_settings import GameConfig

class Tournament:
    def __init__(self, config: GameConfig):
        self.config = config
        self.current_round = 1
        self.results: List[Dict] = []
        self.snake1_wins = 0
        self.snake2_wins = 0
        self.total_snake1_apples = 0
        self.total_snake2_apples = 0
        self.snake1_name: Optional[str] = None
        self.snake2_name: Optional[str] = None
        self.crashed_rounds = 0
        self.draw_rounds = 0
        self.snake1_total_traps = 0
        self.snake2_total_traps = 0
        self.snake1_total_collisions = 0
        self.snake2_total_collisions = 0
    
    def record_round(self, 
                winner: Optional[str], 
                snake1_score: int, 
                snake2_score: int,
                snake1_traps_hit: int = 0,
                snake2_traps_hit: int = 0,
                snake1_collisions: int = 0,
                snake2_collisions: int = 0,
                snake1_collision_types: List[str] = None,
                snake2_collision_types: List[str] = None,
                time_remaining: float = 0.0) -> None:
        """Record comprehensive round results"""
        if snake1_collision_types is None:
            snake1_collision_types = []
        if snake2_collision_types is None:
            snake2_collision_types = []
            
        is_draw = winner is None
        is_crash = snake1_score == 0 and snake2_score == 0
        
        if is_draw:
            self.draw_rounds += 1
        if is_crash:
            self.crashed_rounds += 1
            
        # Update totals
        self.total_snake1_apples += snake1_score
        self.total_snake2_apples += snake2_score
        self.snake1_total_traps += snake1_traps_hit
        self.snake2_total_traps += snake2_traps_hit
        self.snake1_total_collisions += snake1_collisions
        self.snake2_total_collisions += snake2_collisions
        
        # Only update win counts here
        if winner == self.snake1_name:
            self.snake1_wins += 1
        elif winner == self.snake2_name:
            self.snake2_wins += 1
            
        self.results.append({
            "round": self.current_round,
            "timestamp": datetime.now().isoformat(),
            "winner": winner,
            "snake1_score": snake1_score,
            "snake2_score": snake2_score,
            "snake1_traps_hit": snake1_traps_hit,
            "snake2_traps_hit": snake2_traps_hit,
            "snake1_collisions": snake1_collisions,
            "snake2_collisions": snake2_collisions,
            "snake1_collision_types": ','.join(snake1_collision_types),
            "snake2_collision_types": ','.join(snake2_collision_types),
            "time_remaining": time_remaining,
            "is_draw": is_draw,
            "is_crash": is_crash,
            "total_snake1_apples": self.total_snake1_apples,
            "total_snake2_apples": self.total_snake2_apples
        })
        self.current_round += 1
    
    def save_to_csv(self, filename: str = "tournament_results.csv") -> None:
        """Save all tournament results to a CSV file"""
        fieldnames = [
            "round", "timestamp", "winner", 
            "snake1_score", "snake2_score",
            "snake1_traps_hit", "snake2_traps_hit",
            "snake1_collisions", "snake2_collisions",
            "snake1_collision_types", "snake2_collision_types",
            "time_remaining", "is_draw", "is_crash",
            "total_snake1_apples", "total_snake2_apples"
        ]
        
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"Tournament results saved to {filename}")
    
    def get_winner(self) -> Optional[str]:
        """Determine the tournament winner with comprehensive criteria"""
        # Early victory by point difference
        if (len(self.results) >= self.config.min_rounds_for_early_victory and
            abs(self.total_snake1_apples - self.total_snake2_apples) >= self.config.early_victory_diff):
            return self.snake1_name if self.total_snake1_apples > self.total_snake2_apples else self.snake2_name
            
        # Must have completed all rounds to determine normal winner
        if len(self.results) < self.config.max_rounds:
            return None
            
        # Normal victory conditions after all rounds
        if self.snake1_wins > self.snake2_wins:
            return self.snake1_name
        elif self.snake2_wins > self.snake1_wins:
            return self.snake2_name
        else:
            # Tiebreaker by apples
            if self.total_snake1_apples > self.total_snake2_apples:
                return self.snake1_name
            elif self.total_snake2_apples > self.total_snake1_apples:
                return self.snake2_name
        
        # Complete draw
        return None
    
    def is_tournament_over(self) -> bool:
        """Check if tournament should end with new conditions"""
        # Early victory by point difference
        if (len(self.results) >= self.config.min_rounds_for_early_victory and
            abs(self.total_snake1_apples - self.total_snake2_apples) >= self.config.early_victory_diff):
            return True
            
        # Normal end conditions - must complete all rounds unless early victory
        if len(self.results) >= self.config.max_rounds:
            return True
            
        return False
        