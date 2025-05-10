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
        
        if winner == "snake1":
            self.snake1_wins += 1
        elif winner == "snake2":
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
        if self.snake1_wins > self.snake2_wins:
            return "snake1"
        elif self.snake2_wins > self.snake1_wins:
            return "snake2"
        return None
    
    def is_tournament_over(self) -> bool:
        """Check if tournament is complete"""
        max_rounds = self.config.max_rounds
        if self.current_round > max_rounds:
            return True
        
        # Check if one snake has unassailable lead
        remaining_rounds = max_rounds - self.current_round + 1
        if abs(self.snake1_wins - self.snake2_wins) > remaining_rounds:
            return True
            
        return False