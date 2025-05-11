import csv
from datetime import datetime
from typing import List, Dict, Optional
from game_settings import GameConfig

class Tournament:
    def __init__(self, config: GameConfig):
        self.config = config
        self.results: List[Dict] = []
        self.current_round = 1
        self.snake1_wins = 0
        self.snake2_wins = 0
        self.snake1_name: str = None
        self.snake2_name: str = None
    
    def record_round(self, winner: Optional[str], 
                   snake1_score: int, 
                   snake2_score: int) -> None:
        """Record the results of a single round"""
        result = {
            "round": self.current_round,
            "timestamp": datetime.now().isoformat(),
            "winner": winner,
            "snake1_score": snake1_score,
            "snake2_score": snake2_score
        }
        self.results.append(result)
        
        if winner == self.snake1_name:
            self.snake1_wins += 1
        elif winner == self.snake2_name:
            self.snake2_wins += 1
            
        self.current_round += 1
    
    def save_to_csv(self, filename: str = "tournament_results.csv") -> None:
        """Save tournament results to CSV file"""
        if not self.results:
            return
            
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.results[0].keys())
            writer.writeheader()
            writer.writerows(self.results)
    
    def get_winner(self) -> Optional[str]:
        """Determine the tournament winner"""
        total_s1 = sum(r["snake1_score"] for r in self.results)
        total_s2 = sum(r["snake2_score"] for r in self.results)
        
        # First check round wins
        if self.snake1_wins > self.snake2_wins:
            return self.snake1_name
        elif self.snake2_wins > self.snake1_wins:
            return self.snake2_name
        
        # If round wins are equal, check total score
        if total_s1 > total_s2:
            return self.snake1_name
        elif total_s2 > total_s1:
            return self.snake2_name
        
        # If still equal, no winner
        return None
    
    def is_tournament_over(self) -> bool:
        """Check if tournament is complete"""
        # Tournament ends when max rounds reached
        if self.current_round > self.config.max_rounds:
            # Check if we need a tiebreaker
            if self.snake1_wins != self.snake2_wins:
                return True
            # If scores are equal but wins aren't, we need tiebreaker
            total_s1 = sum(r["snake1_score"] for r in self.results)
            total_s2 = sum(r["snake2_score"] for r in self.results)
            if total_s1 == total_s2 and self.snake1_wins != self.snake2_wins:
                return False
            return True
        
        # Or when one snake has unassailable lead
        rounds_remaining = self.config.max_rounds - self.current_round + 1
        if abs(self.snake1_wins - self.snake2_wins) > rounds_remaining:
            return True
            
        return False