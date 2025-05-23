import os
import importlib
import sys
from typing import List, Dict, Tuple
import csv
from datetime import datetime
from tournament import Tournament
from game_settings import GameConfig

class Contest:
    def __init__(self):
        self.bots: List[Dict] = []  # Stores all bot classes and metadata
        self.leaderboard: List[Dict] = []
        self.config = GameConfig()
        self.config.max_rounds = 3  # Best of 3 matches
        self.config.round_time = 60  # 60 seconds per match
        self.tournament_results = []

    def discover_bots(self) -> List[Dict]:
        """Scan AI_Course_Contest folder for valid bot files"""
        bot_files = []
        bots = []
        
        if not os.path.exists("AI_Course_Contest"):
            os.makedirs("AI_Course_Contest")
            raise Exception("AI_Course_Contest folder created - please add bot files")

        for file in os.listdir("AI_Course_Contest"):
            if file.endswith(".py") and file.count("_") >= 2:  # name1_name2_bot.py format
                bot_files.append(file)

        for bot_file in bot_files:
            try:
                # Extract names from filename
                parts = bot_file[:-3].split("_")  # Remove .py and split
                name1, name2 = parts[0], parts[1]
                
                # Import the module
                module_name = f"AI_Course_Contest.{bot_file[:-3]}"
                spec = importlib.util.spec_from_file_location(module_name, f"AI_Course_Contest/{bot_file}")
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Get the UserBot class
                if hasattr(module, "UserBot"):
                    bot_class = module.UserBot
                    bot_name = getattr(bot_class, "name", f"{name1}_{name2}")
                    
                    bots.append({
                        "class": bot_class,
                        "name": bot_name,
                        "filename": bot_file,
                        "authors": f"{name1} & {name2}",
                        "wins": 0,
                        "losses": 0,
                        "points": 0  # 3 for win, 1 for draw
                    })
                    
            except Exception as e:
                print(f"Error loading {bot_file}: {str(e)}")
                continue

        if not bots:
            raise Exception("No valid bots found in AI_Course_Contest folder")
            
        self.bots = bots
        return bots

    def run_match(self, bot1: Dict, bot2: Dict) -> Dict:
        """Run a match between two bots and return results"""
        from snake_game import SnakeGame  # Import here to avoid circular imports
        
        print(f"\n=== MATCH: {bot1['name']} vs {bot2['name']} ===")
        
        game = SnakeGame()
        game.bot1 = bot1["class"]()
        game.bot2 = bot2["class"]()
        game.tournament = Tournament(self.config)
        
        # Run the game
        game.run()  # This will handle the match internally
        
        # Get results
        result = {
            "bot1": bot1["name"],
            "bot2": bot2["name"],
            "bot1_score": game.tournament.total_snake1_apples,
            "bot2_score": game.tournament.total_snake2_apples,
            "winner": game.final_winner,
            "rounds_played": len(game.tournament.results)
        }
        
        # Update bot stats
        if result["winner"] == bot1["name"]:
            bot1["wins"] += 1
            bot1["points"] += 3
            bot2["losses"] += 1
        elif result["winner"] == bot2["name"]:
            bot2["wins"] += 1
            bot2["points"] += 3
            bot1["losses"] += 1
        else:  # Draw
            bot1["points"] += 1
            bot2["points"] += 1
            
        self.tournament_results.append(result)
        return result

    def round_robin_tournament(self):
        """Run a round-robin tournament where each bot plays every other bot"""
        self.discover_bots()
        num_bots = len(self.bots)
        
        print(f"\nStarting Round Robin Tournament with {num_bots} bots")
        
        for i in range(num_bots):
            for j in range(i+1, num_bots):
                self.run_match(self.bots[i], self.bots[j])
        
        self.update_leaderboard()
        self.save_results()

    def knockout_tournament(self):
        """Run a knockout tournament with losers bracket"""
        self.discover_bots()
        bots = self.bots.copy()
        num_bots = len(bots)
        
        if num_bots % 2 != 0:
            # Add a bye if odd number of bots
            bots.append({"name": "BYE", "class": None, "wins": 0, "losses": 0, "points": 0})
            num_bots += 1
        
        winners = []
        losers = []
        
        print(f"\nStarting Knockout Tournament with {num_bots} bots")
        
        # Initial matches
        for i in range(0, num_bots, 2):
            if i+1 >= num_bots:
                # Handle odd case (shouldn't happen due to bye)
                winners.append(bots[i])
                continue
                
            if bots[i]["name"] == "BYE":
                winners.append(bots[i+1])
                continue
            if bots[i+1]["name"] == "BYE":
                winners.append(bots[i])
                continue
                
            result = self.run_match(bots[i], bots[i+1])
            if result["winner"] == bots[i]["name"]:
                winners.append(bots[i])
                losers.append(bots[i+1])
            else:
                winners.append(bots[i+1])
                losers.append(bots[i])
        
        # Losers bracket matches
        if losers:
            print("\n=== LOSERS BRACKET ===")
            new_losers = []
            advancing_losers = []
            
            # Have losers play each other
            for i in range(0, len(losers), 2):
                if i+1 >= len(losers):
                    advancing_losers.append(losers[i])
                    continue
                    
                result = self.run_match(losers[i], losers[i+1])
                if result["winner"] == losers[i]["name"]:
                    advancing_losers.append(losers[i])
                    new_losers.append(losers[i+1])
                else:
                    advancing_losers.append(losers[i+1])
                    new_losers.append(losers[i])
            
            # Winners of losers bracket join main winners
            winners.extend(advancing_losers)
        
        self.update_leaderboard()
        self.save_results()

    def update_leaderboard(self):
        """Update the leaderboard based on current results"""
        self.leaderboard = sorted(
            self.bots,
            key=lambda x: (-x["points"], -x["wins"], x["losses"])
        )
        
        # Add rank position
        for i, bot in enumerate(self.leaderboard):
            bot["rank"] = i + 1

    def save_results(self, filename: str = "contest_results.csv"):
        """Save tournament results to CSV"""
        if not self.leaderboard:
            self.update_leaderboard()
            
        fieldnames = [
            "rank", "name", "authors", "wins", "losses", "points",
            "filename"
        ]
        
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for bot in self.leaderboard:
                writer.writerow({
                    "rank": bot["rank"],
                    "name": bot["name"],
                    "authors": bot["authors"],
                    "wins": bot["wins"],
                    "losses": bot["losses"],
                    "points": bot["points"],
                    "filename": bot["filename"]
                })
        
        print(f"\nResults saved to {filename}")

    def print_leaderboard(self):
        """Print a formatted leaderboard to console"""
        if not self.leaderboard:
            self.update_leaderboard()
            
        print("\n=== FINAL LEADERBOARD ===")
        print(f"{'Rank':<5} {'Bot Name':<20} {'Authors':<20} {'Wins':<5} {'Losses':<7} {'Points':<7}")
        print("-"*65)
        
        for bot in self.leaderboard:
            print(f"{bot['rank']:<5} {bot['name']:<20} {bot['authors']:<20} "
                  f"{bot['wins']:<5} {bot['losses']:<7} {bot['points']:<7}")

if __name__ == "__main__":
    contest = Contest()
    
    print("Select tournament type:")
    print("1. Round Robin (each bot plays every other bot)")
    print("2. Knockout (single elimination with losers bracket)")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        contest.round_robin_tournament()
    elif choice == "2":
        contest.knockout_tournament()
    else:
        print("Invalid choice, defaulting to Round Robin")
        contest.round_robin_tournament()
    
    contest.print_leaderboard()