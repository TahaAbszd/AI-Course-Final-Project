from typing import Tuple, Optional, List
from game_settings import Snake, Food, Direction, get_distance, is_safe
import random
import math


class Bot:
    """
    Base class for all snake agents.
    Subclasses must implement the decide_move() method.
    Adding Some Function for getting_possible_moves and so on and changing other bot classes
    """
    def __init__(self, name: str = "BaseBot"):
        self.name = name
        self.config = {
            'food_weight': 100,
            'mobility_weight': 20,
            'danger_weight': 150,
            'prediction_depth': 3
        }
    
    def decide_move(self, 
                   snake: Snake, 
                   food: Food, 
                   opponent: Optional[Snake] = None) -> Tuple[int, int]:
        """
        Determine the next move for the snake.
        Args:
            snake: The snake being controlled
            food: Food objects in the game
            opponent: Optional opponent snake
        Returns:
            Tuple[int, int]: Direction vector (dx, dy)
        """
        raise NotImplementedError

class RandomBot(Bot):
    """Moves randomly"""
    def __init__(self):
        super().__init__()
        self.name = "RandomBot"
    
    def decide_move(self, snake, food, opponent=None):
        possible_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        possible_moves = [m for m in possible_moves if m != Direction.opposite(snake.direction)]
        return random.choice(possible_moves)

class GreedyBot(Bot):
    """Goes for nearest food"""
    def __init__(self):
        super().__init__()
        self.name = "GreedyBot"
    
    def decide_move(self, snake, food, opponent=None):
        head_pos = snake.get_head_position()
        current_dir = snake.direction

        if not food.positions:
            return current_dir

        # Find closest food
        closest_food = min(food.positions, key=lambda pos: get_distance(head_pos, pos))

        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        possible_moves = [move for move in possible_moves if move != (-current_dir[0], -current_dir[1])]

        best_move = current_dir
        best_score = -float('inf')

        for move in possible_moves:
            new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
            if not is_safe(snake, new_head, opponent):
                continue

            # Calculate food proximity score
            food_dist = get_distance(new_head, closest_food)
            food_score = 1 / (food_dist + 1e-5) * 100  # Avoid division by zero

            # Calculate mobility score
            mobility = 0
            next_moves = [m for m in [(1,0), (-1,0), (0,1), (0,-1)] if m != (-move[0], -move[1])]
            for next_move in next_moves:
                next_head_pos = [new_head[0] + next_move[0], new_head[1] + next_move[1]]
                if is_safe(snake, next_head_pos, opponent):
                    mobility += 1

            # Calculate danger score
            danger = 0
            if opponent and opponent.alive:
                other_head = opponent.get_head_position()
                dist_to_other = get_distance(new_head, other_head)
                if dist_to_other < 4 and len(opponent.segments) >= len(snake.segments):
                    danger = 1
                    # Predict other snake's movement
                    other_dir = opponent.direction
                    predicted_other_head = [other_head[0] + other_dir[0], other_head[1] + other_dir[1]]
                    if new_head == predicted_other_head:
                        danger += 1

            total_score = food_score + mobility * 15 - danger * 100
            if total_score > best_score:
                best_score = total_score
                best_move = move

        return best_move
        

class StrategicBot(Bot):
    """Avoids opponent and traps"""
    def __init__(self):
        super().__init__()
        self.name = "StrategicBot"
    
    def decide_move(self, snake, food, opponent=None):
        head_pos = snake.get_head_position()
        current_dir = snake.direction

        if not food.positions:
            return current_dir

        # Find safest food considering other snake
        food_scores = []
        for f in food.positions:
            base_score = 1 / (get_distance(head_pos, f) + 1e-5)
            # Penalize food close to other snake
            if opponent:
                other_dist = get_distance(f, opponent.get_head_position())
                base_score *= max(0.1, 1 - (1 / (other_dist + 1)))
            food_scores.append(base_score)
        target_food = food.positions[food_scores.index(max(food_scores))]

        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        possible_moves = [move for move in possible_moves if move != (-current_dir[0], -current_dir[1])]

        best_move = current_dir
        best_score = -float('inf')

        for move in possible_moves:
            new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
            if not is_safe(snake, new_head, opponent):
                continue

            # Food proximity
            food_dist = get_distance(new_head, target_food)
            food_score = 1 / (food_dist + 1e-5) * 100

            # Mobility
            mobility = 0
            next_moves = [m for m in [(1,0), (-1,0), (0,1), (0,-1)] if m != (-move[0], -move[1])]
            for next_move in next_moves:
                next_head_pos = [new_head[0] + next_move[0], new_head[1] + next_move[1]]
                if is_safe(snake, next_head_pos, opponent):
                    mobility += 1

            # Advanced danger detection
            danger = 0
            if opponent and opponent.alive:
                # Check if other snake is targeting same area
                other_path = []
                temp_head = opponent.get_head_position()
                for _ in range(3):  # Predict next 3 moves
                    temp_head = [temp_head[0] + opponent.direction[0], 
                                temp_head[1] + opponent.direction[1]]
                    other_path.append(temp_head)
                if new_head in other_path:
                    danger += 2

                # Space around other snake
                other_space = 0
                for m in [(1,0), (-1,0), (0,1), (0,-1)]:
                    check_pos = [temp_head[0] + m[0], temp_head[1] + m[1]]
                    if is_safe(opponent, check_pos, snake):
                        other_space += 1
                if other_space <= 1:  # Other snake in tight space
                    danger -= 1  # Less dangerous

            total_score = food_score + mobility * 20 - danger * 150
            if total_score > best_score:
                best_score = total_score
                best_move = move

        return best_move

# User implements their bot by extending the Bot class
class CustomBot(Bot):
    def __init__(self):
        super().__init__()
        self.name = "MyCustomBot"
    
    def decide_move(self, snake, food, opponent=None):
        # Implement your custom logic here
        pass
from typing import Tuple, Optional, List
from game_settings import Snake, Food, Direction, get_distance, is_safe, Trap
import random
import math
from collections import deque

# سایر کلاس‌ها (Bot, RandomBot, GreedyBot, StrategicBot, CustomBot) بدون تغییر باقی می‌مانند
# فقط کلاس UserBot اصلاح می‌شود
from typing import Tuple, Optional, List
from game_settings import Snake, Food, Direction, get_distance, is_safe, Trap
import random
import math
from collections import deque

# سایر کلاس‌ها (Bot, RandomBot, GreedyBot, StrategicBot, CustomBot) بدون تغییر باقی می‌مانند
from typing import Tuple, Optional, List
from game_settings import Snake, Food, Direction, get_distance, is_safe, Trap, GRID_WIDTH, GRID_HEIGHT
import random
import math
from collections import deque

# سایر کلاس‌ها (Bot, RandomBot, GreedyBot, StrategicBot, CustomBot) بدون تغییر باقی می‌مانند
from typing import Tuple, Optional, List
from game_settings import Snake, Food, Direction, get_distance, is_safe, Trap, GRID_WIDTH, GRID_HEIGHT
import random
import math
from collections import deque

# سایر کلاس‌ها (Bot, RandomBot, GreedyBot, StrategicBot, CustomBot) بدون تغییر باقی می‌مانند
from typing import Optional, Tuple, List
from collections import deque

class UserBot(Bot):
    def __init__(self):
        super().__init__()
        self.name = "SuperBot"
        self.base_depth = 2
        self.max_depth = 3
        self.config['food_weight'] = 300
        self.config['mobility_weight'] = 40
        self.config['danger_weight'] = 120
        self.config['trap_weight'] = 100
        self.config['shield_bonus'] = 50
        self.config['opponent_trap_bonus'] = 30

    def decide_move(self, snake: Snake, food: Food, opponent: Optional[Snake] = None, traps: Optional[Trap] = None) -> Tuple[int, int]:
        head_pos = snake.get_head_position()
        min_dist_to_opponent = float('inf')
        if opponent and opponent.alive:
            min_dist_to_opponent = get_distance(head_pos, opponent.get_head_position())

        depth = self.base_depth
        if len(food.positions) > 10 and len(snake.segments) < 10 and min_dist_to_opponent > 5:
            depth = self.max_depth

        possible_moves = self.get_possible_moves(snake)
        if food.positions:
            closest_food = min(food.positions, key=lambda pos: get_distance(head_pos, pos))
            possible_moves.sort(key=lambda move: get_distance([head_pos[0] + move[0], head_pos[1] + move[1]], closest_food))

        best_score, best_move = self.minimax(snake, opponent, food, traps, depth=depth, alpha=-float('inf'), beta=float('inf'), is_max=True)
        if best_move is None:
            safe_moves = [move for move in possible_moves if is_safe(snake, [head_pos[0] + move[0], head_pos[1] + move[1]], opponent)]
            return safe_moves[0] if safe_moves else Direction.RIGHT
        return best_move

    def minimax(self, snake: Snake, opponent: Optional[Snake], food: Food, traps: Optional[Trap], depth: int, alpha: float, beta: float, is_max: bool) -> Tuple[float, Optional[Tuple[int, int]]]:
        if depth == 0 or not snake.alive or (opponent and not opponent.alive):
            return self.evaluate(snake, opponent, food, traps), None

        possible_moves = self.get_possible_moves(snake if is_max else opponent)
        head_pos = snake.get_head_position() if is_max else (opponent.get_head_position() if opponent else [0, 0])

        if food.positions:
            closest_food = min(food.positions, key=lambda pos: get_distance(head_pos, pos))
            possible_moves.sort(key=lambda move: get_distance([head_pos[0] + move[0], head_pos[1] + move[1]], closest_food))

        best_move = None
        if is_max:
            max_eval = -float('inf')
            for move in possible_moves:
                new_snake = self.simulate_move(snake, move, food, traps, opponent)
                eval_score, _ = self.minimax(new_snake, opponent, food, traps, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in possible_moves:
                new_opponent = self.simulate_move(opponent, move, food, traps, snake)
                eval_score, _ = self.minimax(snake, new_opponent, food, traps, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_possible_moves(self, snake: Snake) -> List[Tuple[int, int]]:
        current_dir = snake.direction if snake.direction is not None else Direction.RIGHT
        possible_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        return [move for move in possible_moves if move != Direction.opposite(current_dir)]

    def simulate_move(self, snake: Snake, move: Tuple[int, int], food: Food, traps: Optional[Trap], opponent: Optional[Snake] = None) -> Snake:
        head_pos = snake.get_head_position()
        new_snake = Snake(snake.color_primary, snake.color_secondary, head_pos[0], head_pos[1], snake.agent_id)
        new_snake.segments = deque(snake.segments)
        new_snake.direction = move
        new_snake.next_direction = move
        new_snake.length = snake.length
        new_snake.grow = snake.grow
        new_snake.score = snake.score
        new_snake.alive = snake.alive
        new_snake.shield_timer = snake.shield_timer
        new_snake.traps_hit = snake.traps_hit
        new_snake.collisions = snake.collisions
        new_snake.collision_types = snake.collision_types[:]
        new_snake.update(1.0 / snake.speed)

        if new_snake.alive:
            new_head = new_snake.get_head_position()
            if any(new_head == list(pos) for pos in food.positions):
                new_snake.grow += new_snake.config.growth_per_food
                new_snake.score += 1

            if traps and any(new_head == list(pos) for pos in traps.positions):
                new_snake.score = max(0, new_snake.score - new_snake.config.trap_penalty)
                for _ in range(new_snake.config.trap_segment_penalty):
                    if len(new_snake.segments) > new_snake.config.min_snake_length:
                        if new_snake.grow > 0:
                            new_snake.grow -= 1
                        else:
                            new_snake.segments.pop()
                        new_snake.length -= 1
                new_snake.shield_timer = new_snake.config.shield_duration
                new_snake.traps_hit += 1

            if opponent and opponent.alive and new_snake.shield_timer <= 0:
                if new_head == opponent.get_head_position():
                    new_snake.collisions += 1
                    new_snake.collision_types.append("head-to-head")
                    penalty = new_snake.config.head_collision_penalty
                    if new_snake.score < opponent.score:
                        new_snake.score = max(0, new_snake.score - penalty)
                        for _ in range(new_snake.config.collision_segment_penalty):
                            if len(new_snake.segments) > new_snake.config.min_snake_length:
                                new_snake.segments.pop()
                                new_snake.length -= 1
                        new_snake.shield_timer = new_snake.config.shield_duration
                    elif new_snake.score == opponent.score:
                        new_snake.score = max(0, new_snake.score - penalty)
                        for _ in range(new_snake.config.collision_segment_penalty):
                            if len(new_snake.segments) > new_snake.config.min_snake_length:
                                new_snake.segments.pop()
                                new_snake.length -= 1
                        new_snake.shield_timer = new_snake.config.shield_duration
                else:
                    opponent_body = list(opponent.segments)[1:]
                    if new_head in opponent_body:
                        new_snake.collisions += 1
                        new_snake.collision_types.append("body")
                        new_snake.score = max(0, new_snake.score - new_snake.config.body_collision_penalty)
                        for _ in range(new_snake.config.collision_segment_penalty):
                            if len(new_snake.segments) > new_snake.config.min_snake_length:
                                new_snake.segments.pop()
                                new_snake.length -= 1
                            new_snake.shield_timer = new_snake.config.shield_duration
        return new_snake

    def evaluate(self, snake: Snake, opponent: Optional[Snake], food: Food, traps: Optional[Trap]) -> float:
        if not snake.alive:
            return -1000
        if opponent and not opponent.alive:
            return 1000

        head_pos = snake.get_head_position()
        if not food.positions:
            return 0

        food_scores = []
        for f in food.positions:
            base_score = 1 / (get_distance(head_pos, f) + 1e-5)
            if opponent and opponent.alive:
                other_dist = get_distance(f, opponent.get_head_position())
                base_score *= max(0.1, 1 - (1 / (other_dist + 1)))
            food_scores.append(base_score)

        closest_food = food.positions[food_scores.index(max(food_scores))]
        food_dist = get_distance(head_pos, closest_food)
        food_score = 1 / (food_dist + 1e-5) * self.config['food_weight']

        mobility = 0
        for move in self.get_possible_moves(snake):
            new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
            if is_safe(snake, new_head, opponent):
                mobility += 1

        danger = 0
        opponent_trap_bonus = 0
        if opponent and opponent.alive:
            other_head = opponent.get_head_position()
            dist_to_other = get_distance(head_pos, other_head)
            if dist_to_other < 4 and len(opponent.segments) >= len(snake.segments):
                danger += 1.5

            other_path = [other_head]
            temp_head = other_head[:]
            for _ in range(4):
                temp_head = [temp_head[0] + opponent.direction[0], temp_head[1] + opponent.direction[1]]
                if is_safe(opponent, temp_head, snake):
                    other_path.append(temp_head)
            if head_pos in other_path:
                danger += 2

            opponent_mobility = 0
            for m in self.get_possible_moves(opponent):
                check_pos = [other_head[0] + m[0], other_head[1] + m[1]]
                if is_safe(opponent, check_pos, snake):
                    opponent_mobility += 1
            opponent_trap_bonus = self.config['opponent_trap_bonus'] if opponent_mobility <= 1 else 0

        trap_danger = 0
        if traps and traps.positions:
            closest_trap = min(traps.positions, key=lambda pos: get_distance(head_pos, pos))
            trap_dist = get_distance(head_pos, closest_trap)
            if trap_dist < 4:   
                '''test'''
                trap_danger += 2 / (trap_dist + 1e-5) * self.config['trap_weight']

        shield_bonus = self.config['shield_bonus'] if snake.shield_timer > 0 else 0
        length_penalty = len(snake.segments) * 5 if len(snake.segments) > 10 else 0

        total_score = (
            food_score
            + mobility * self.config['mobility_weight']
            - danger * self.config['danger_weight']
            - trap_danger
            + shield_bonus
            + opponent_trap_bonus
            - length_penalty
        )
        return total_score
