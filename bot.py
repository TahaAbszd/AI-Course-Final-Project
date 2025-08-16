from typing import Tuple, Optional, List
from game_settings import Snake, Food, Direction, get_distance, is_safe, Trap, GRID_WIDTH, GRID_HEIGHT
import random
import math
from collections import deque
import heapq
import time

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

class CustomBot(Bot):
    def __init__(self):
        super().__init__()
        self.name = "MyCustomBot"
        self.food_weight = 200.0
        self.area_weight = 6.0
        self.danger_weight = 220.0
        self.length_weight = 40.0
        self.astar_bonus = 120.0
        self.trap_penalty = 350.0
        self.max_minimax_depth = 2
        self.max_astar_nodes = 800
        self.max_bfs_nodes = 300
        self.time_budget = 0.04
        self.randomness = 0.02

    def decide_move(self, snake: Snake, food: Food, opponent: Optional[Snake] = None, traps: Optional[Trap] = None) -> Tuple[int, int]:
        start_t = time.time()
        head = snake.get_head_position()
        current_dir = snake.direction if snake.direction is not None else Direction.RIGHT

        all_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        possible_moves = [m for m in all_moves if m != Direction.opposite(current_dir)]

        safe_moves = []
        for m in possible_moves:
            nh = [head[0] + m[0], head[1] + m[1]]
            if is_safe(snake, nh, opponent):
                if traps and traps.positions and any(nh == [t[0], t[1]] for t in traps.positions):
                    continue
                safe_moves.append(m)

        if not safe_moves:
            for m in possible_moves:
                nh = [head[0] + m[0], head[1] + m[1]]
                if 0 <= nh[0] < GRID_WIDTH and 0 <= nh[1] < GRID_HEIGHT:
                    safe_moves.append(m)

        if not safe_moves:
            return possible_moves[0] if possible_moves else Direction.RIGHT

        nearest_food = None
        best_af_path = []
        if food.positions:
            foods_sorted = sorted(food.positions, key=lambda fpos: get_distance(head, fpos))[:6]
            obstacles = set(tuple(s) for s in list(snake.segments)[1:])
            if opponent and opponent.alive:
                obstacles.update(tuple(s) for s in list(opponent.segments))
            if traps and traps.positions:
                obstacles.update(tuple(t) for t in traps.positions)

            best_len = None
            for fpos in foods_sorted:
                path = self._astar(head, list(fpos), obstacles, self.max_astar_nodes)
                if path:
                    if best_len is None or len(path) < best_len:
                        best_len = len(path)
                        best_af_path = path
                        nearest_food = fpos

        if best_af_path and len(best_af_path) > 1:
            next_pos = best_af_path[1]
            move_to_follow = (next_pos[0] - head[0], next_pos[1] - head[1])
            if move_to_follow in safe_moves:
                score = self._minimax_score(snake, opponent, food, traps, move_to_follow, self.max_minimax_depth, start_t)
                if score > -1e6:
                    return move_to_follow

        best_move = None
        best_score = -float('inf')
        for move in safe_moves:
            if time.time() - start_t > self.time_budget:
                break
            score = self._minimax_score(snake, opponent, food, traps, move, self.max_minimax_depth, start_t)
            score += (random.random() * self.randomness)
            if score > best_score:
                best_score = score
                best_move = move

        if best_move is None:
            best_move = random.choice(safe_moves)

        return best_move

    def _astar(self, start: List[int], target: List[int], obstacles: set, max_nodes: int = 800) -> List[List[int]]:
        start_tup = tuple(start)
        target_tup = tuple(target)
        open_heap = []
        gscore = {start_tup: 0}
        fscore = {start_tup: get_distance(start, target)}
        heapq.heappush(open_heap, (fscore[start_tup], start_tup, [list(start_tup)]))
        closed = set()
        nodes = 0

        while open_heap and nodes < max_nodes:
            nodes += 1
            _, current, path = heapq.heappop(open_heap)
            if current == target_tup:
                return path
            if current in closed:
                continue
            closed.add(current)
            cx, cy = current
            for move in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = cx + move[0], cy + move[1]
                nt = (nx, ny)
                if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                    continue
                if nt in obstacles:
                    continue
                tentative_g = gscore[current] + 1
                if nt not in gscore or tentative_g < gscore[nt]:
                    gscore[nt] = tentative_g
                    h = get_distance((nx, ny), target)
                    heapq.heappush(open_heap, (tentative_g + h, nt, path + [[nx, ny]]))
        return []

    def _flood_fill_area(self, head_pos: List[int], my_segments: List[List[int]], other_segments: List[List[int]], max_nodes: int = 300) -> int:
        visited = set()
        q = deque()
        start = tuple(head_pos)
        visited.add(start)
        q.append(start)
        obstacles = set(tuple(s) for s in my_segments) | set(tuple(s) for s in other_segments)
        count = 0
        nodes = 0
        while q and nodes < max_nodes:
            nodes += 1
            pos = q.popleft()
            count += 1
            x, y = pos
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                    continue
                nt = (nx, ny)
                if nt in visited or nt in obstacles:
                    continue
                visited.add(nt)
                q.append(nt)
        return count

    def _predict_opponent_next_heads(self, opponent: Optional[Snake], steps: int = 3) -> List[List[int]]:
        path = []
        if not opponent or not opponent.alive:
            return path
        pos = opponent.get_head_position()[:]
        dir_ = opponent.direction
        for _ in range(steps):
            nxt = [pos[0] + dir_[0], pos[1] + dir_[1]]
            if not (0 <= nxt[0] < GRID_WIDTH and 0 <= nxt[1] < GRID_HEIGHT):
                break
            path.append(nxt)
            pos = nxt
        return path

    def _simulate_step(self, snake_head: List[int], snake_body: List[List[int]], move: Tuple[int,int]) -> (List[int], List[List[int]]):
        new_head = [snake_head[0] + move[0], snake_head[1] + move[1]]
        new_body = [new_head] + snake_body[:-1] if len(snake_body) > 0 else [new_head]
        return new_head, new_body

    def _available_moves_from(self, head: List[int], body: List[List[int]], other_body: List[List[int]]) -> List[Tuple[int,int]]:
        moves = []
        for m in [(1,0),(-1,0),(0,1),(0,-1)]:
            nh = [head[0] + m[0], head[1] + m[1]]
            if not (0 <= nh[0] < GRID_WIDTH and 0 <= nh[1] < GRID_HEIGHT):
                continue
            if nh in body[1:]:
                continue
            if nh in other_body:
                continue
            moves.append(m)
        return moves

    def _minimax_score(self, snake: Snake, opponent: Optional[Snake], food: Food, traps: Optional[Trap], first_move: Tuple[int,int], depth: int = 3, start_time: float = 0.0) -> float:
        my_head = snake.get_head_position()[:]
        my_body = [seg[:] for seg in snake.segments]
        opp_head = opponent.get_head_position()[:] if opponent and opponent.alive else None
        opp_body = [seg[:] for seg in opponent.segments] if opponent and opponent.alive else []

        traps_set = set(tuple(t) for t in (traps.positions if traps and traps.positions else []))
        food_list = [tuple(f) for f in food.positions] if food and food.positions else []

        my_head, my_body = self._simulate_step(my_head, my_body, first_move)

        if not (0 <= my_head[0] < GRID_WIDTH and 0 <= my_head[1] < GRID_HEIGHT):
            return -1e9
        if tuple(my_head) in set(tuple(s) for s in my_body[1:]):
            return -1e9
        if opp_body and tuple(my_head) in set(tuple(s) for s in opp_body):
            return -1e9
        if tuple(my_head) in traps_set and snake.shield_timer <= 0:
            return -1e7

        def heuristic(my_h, my_b, opp_h, opp_b):
            food_dist = min((get_distance(my_h, f) for f in food_list), default=float('inf'))
            food_score = self.food_weight / (food_dist + 1.0)

            my_area = self._flood_fill_area(my_h, my_b, opp_b, self.max_bfs_nodes)
            opp_area = self._flood_fill_area(opp_h, opp_b, my_b, self.max_bfs_nodes) if opp_h else 0
            area_score = self.area_weight * (my_area - opp_area)

            trap_dist = min((get_distance(my_h, t) for t in traps_set), default=float('inf')) if traps_set else float('inf')
            trap_score = -self.trap_penalty / (trap_dist + 1.0) if trap_dist < 4 else 0

            len_diff = len(my_b) - (len(opp_b) if opp_b else 0)
            length_score = self.length_weight * math.tanh(len_diff / 3.0)

            astar_bonus = 0.0
            if food_list:
                try_targets = sorted(food_list, key=lambda p: get_distance(my_h, p))[:2]
                for t in try_targets:
                    path = self._astar(my_h, list(t), set(tuple(s) for s in my_b) | set(tuple(s) for s in opp_b) | traps_set, max_nodes=120)
                    if path:
                        astar_bonus = self.astar_bonus / (len(path))
                        break

            opp_pred = self._predict_opponent_next_heads(opponent, steps=3) if opponent else []
            min_opp_dist = min((get_distance(my_h, p) for p in opp_pred), default=float('inf'))
            danger_score = 0.0
            if min_opp_dist < 2:
                if opp_b and len(opp_b) >= len(my_b):
                    danger_score = -self.danger_weight * (2.0 - min_opp_dist)
                else:
                    danger_score = -self.danger_weight * 0.4 * (2.0 - min_opp_dist)

            total = food_score + area_score + astar_bonus + length_score + trap_score + danger_score
            return total

        def predict_opponent_moves(opp_h, opp_b, my_b):
            moves = self._available_moves_from(opp_h, opp_b, my_b)
            if not moves:
                return [ (0,0) ]
            scored = []
            for mv in moves:
                nxt = (opp_h[0] + mv[0], opp_h[1] + mv[1])
                dfood = min((get_distance(nxt, f) for f in food_list), default=float('inf'))
                scored.append( (dfood, mv) )
            scored.sort(key=lambda x: x[0])
            return [m for _,m in scored[:3]]

        def minimax(my_h, my_b, opp_h, opp_b, depth, alpha, beta, maximizing_player):
            if time.time() - start_time > self.time_budget:
                return heuristic(my_h, my_b, opp_h, opp_b)
            if depth == 0:
                return heuristic(my_h, my_b, opp_h, opp_b)

            if maximizing_player:
                val = -float('inf')
                moves = self._available_moves_from(my_h, my_b, opp_b)
                if not moves:
                    return -1e6
                for mv in moves:
                    nxt_h, nxt_b = self._simulate_step(my_h, my_b, mv)
                    if not (0 <= nxt_h[0] < GRID_WIDTH and 0 <= nxt_h[1] < GRID_HEIGHT):
                        continue
                    if tuple(nxt_h) in set(tuple(s) for s in nxt_b[1:]):
                        continue
                    if opp_b and tuple(nxt_h) in set(tuple(s) for s in opp_b):
                        continue
                    v = minimax(nxt_h, nxt_b, opp_h, opp_b, depth-1, alpha, beta, False)
                    val = max(val, v)
                    alpha = max(alpha, val)
                    if alpha >= beta:
                        break
                return val
            else:
                val = float('inf')
                if not opp_h:
                    return heuristic(my_h, my_b, opp_h, opp_b)
                moves = predict_opponent_moves(opp_h, opp_b, my_b)
                if not moves:
                    return heuristic(my_h, my_b, opp_h, opp_b)
                for mv in moves:
                    nxt_opp_h, nxt_opp_b = self._simulate_step(opp_h, opp_b, mv)
                    if not (0 <= nxt_opp_h[0] < GRID_WIDTH and 0 <= nxt_opp_h[1] < GRID_HEIGHT):
                        continue
                    if tuple(nxt_opp_h) in set(tuple(s) for s in nxt_opp_b[1:]):
                        continue
                    if tuple(nxt_opp_h) in set(tuple(s) for s in my_b):
                        v = -1e5
                    else:
                        v = minimax(my_h, my_b, nxt_opp_h, nxt_opp_b, depth-1, alpha, beta, True)
                    val = min(val, v)
                    beta = min(beta, val)
                    if alpha >= beta:
                        break
                return val

        try:
            score = minimax(my_head, my_body, opp_head, opp_body, depth, -float('inf'), float('inf'), True)
        except Exception:
            score = -1e6
        return score

    def get_possible_moves(self, snake: Snake) -> List[Tuple[int,int]]:
        cur = snake.direction if snake.direction is not None else Direction.RIGHT
        candidates = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        return [m for m in candidates if m != Direction.opposite(cur)]


class UserBot(Bot):
    def __init__(self, name: str = "ChampionBot"):
        super().__init__(name=name)
        self.food_weight = 200.0
        self.area_weight = 6.0
        self.danger_weight = 220.0
        self.length_weight = 40.0
        self.astar_bonus = 120.0
        self.trap_penalty = 350.0
        self.max_minimax_depth = 2         
        self.max_astar_nodes = 800
        self.max_bfs_nodes = 300
        self.time_budget = 0.04        
        self.randomness = 0.02            

    def decide_move(self, snake: Snake, food: Food, opponent: Optional[Snake] = None, traps: Optional[Trap] = None) -> Tuple[int, int]:

        start_t = time.time()
        head = snake.get_head_position()
        current_dir = snake.direction if snake.direction is not None else Direction.RIGHT

        all_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        possible_moves = [m for m in all_moves if m != Direction.opposite(current_dir)]

        safe_moves = []
        for m in possible_moves:
            nh = [head[0] + m[0], head[1] + m[1]]
            if is_safe(snake, nh, opponent):
                if traps and traps.positions and any(nh == [t[0], t[1]] for t in traps.positions):
                    continue
                safe_moves.append(m)

        if not safe_moves:
            for m in possible_moves:
                nh = [head[0] + m[0], head[1] + m[1]]
                if 0 <= nh[0] < GRID_WIDTH and 0 <= nh[1] < GRID_HEIGHT:
                    safe_moves.append(m)

        if not safe_moves:
            return possible_moves[0] if possible_moves else Direction.RIGHT

        nearest_food = None
        best_af_path = []
        if food.positions:
            foods_sorted = sorted(food.positions, key=lambda fpos: get_distance(head, fpos))[:6]
            obstacles = set(tuple(s) for s in list(snake.segments)[1:])
            if opponent and opponent.alive:
                obstacles.update(tuple(s) for s in list(opponent.segments))
            if traps and traps.positions:
                obstacles.update(tuple(t) for t in traps.positions)

            best_len = None
            for fpos in foods_sorted:
                path = self._astar(head, list(fpos), obstacles, max_nodes=self.max_astar_nodes)
                if path:
                    if best_len is None or len(path) < best_len:
                        best_len = len(path)
                        best_af_path = path
                        nearest_food = fpos

        if best_af_path and len(best_af_path) > 1:
            next_pos = best_af_path[1]
            move_to_follow = (next_pos[0] - head[0], next_pos[1] - head[1])
            if move_to_follow in safe_moves:
                score = self._minimax_score(snake, opponent, food, traps, move_to_follow, depth=2, start_time=start_t)
                if score > -1e6:
                    return move_to_follow

        best_move = None
        best_score = -float('inf')
        for move in safe_moves:
            if time.time() - start_t > self.time_budget:
                break
            score = self._minimax_score(snake, opponent, food, traps, move, depth=self.max_minimax_depth, start_time=start_t)
            score += (random.random() * self.randomness)
            if score > best_score:
                best_score = score
                best_move = move

        if best_move is None:
            best_move = random.choice(safe_moves)

        return best_move

    def _astar(self, start: List[int], target: List[int], obstacles: set, max_nodes: int = 800) -> List[List[int]]:
        start_tup = tuple(start)
        target_tup = tuple(target)
        open_heap = []
        gscore = {start_tup: 0}
        fscore = {start_tup: get_distance(start, target)}
        heapq.heappush(open_heap, (fscore[start_tup], start_tup, [list(start_tup)]))
        closed = set()
        nodes = 0

        while open_heap and nodes < max_nodes:
            nodes += 1
            _, current, path = heapq.heappop(open_heap)
            if current == target_tup:
                return path
            if current in closed:
                continue
            closed.add(current)
            cx, cy = current
            for move in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = cx + move[0], cy + move[1]
                nt = (nx, ny)
                if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                    continue
                if nt in obstacles:
                    continue
                tentative_g = gscore[current] + 1
                if nt not in gscore or tentative_g < gscore[nt]:
                    gscore[nt] = tentative_g
                    h = get_distance((nx, ny), target)
                    heapq.heappush(open_heap, (tentative_g + h, nt, path + [[nx, ny]]))
        return []

    def _flood_fill_area(self, head_pos: List[int], my_segments: List[List[int]], other_segments: List[List[int]], max_nodes: int = 300) -> int:
        visited = set()
        q = deque()
        start = tuple(head_pos)
        visited.add(start)
        q.append(start)
        obstacles = set(tuple(s) for s in my_segments) | set(tuple(s) for s in other_segments)
        count = 0
        nodes = 0
        while q and nodes < max_nodes:
            nodes += 1
            pos = q.popleft()
            count += 1
            x, y = pos
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                    continue
                nt = (nx, ny)
                if nt in visited or nt in obstacles:
                    continue
                visited.add(nt)
                q.append(nt)
        return count

    def _predict_opponent_next_heads(self, opponent: Optional[Snake], steps: int = 3) -> List[List[int]]:
        path = []
        if not opponent or not opponent.alive:
            return path
        pos = opponent.get_head_position()[:]
        dir_ = opponent.direction
        for _ in range(steps):
            nxt = [pos[0] + dir_[0], pos[1] + dir_[1]]
            if not (0 <= nxt[0] < GRID_WIDTH and 0 <= nxt[1] < GRID_HEIGHT):
                break
            path.append(nxt)
            pos = nxt
        return path

    def _simulate_step(self, snake_head: List[int], snake_body: List[List[int]], move: Tuple[int,int]) -> (List[int], List[List[int]]):
        new_head = [snake_head[0] + move[0], snake_head[1] + move[1]]
        new_body = [new_head] + snake_body[:-1] if len(snake_body) > 0 else [new_head]
        return new_head, new_body

    def _available_moves_from(self, head: List[int], body: List[List[int]], other_body: List[List[int]]) -> List[Tuple[int,int]]:
        moves = []
        for m in [(1,0),(-1,0),(0,1),(0,-1)]:
            nh = [head[0] + m[0], head[1] + m[1]]
            if not (0 <= nh[0] < GRID_WIDTH and 0 <= nh[1] < GRID_HEIGHT):
                continue
            if nh in body[1:]:
                continue
            if nh in other_body:
                continue
            moves.append(m)
        return moves

    def _minimax_score(self, snake: Snake, opponent: Optional[Snake], food: Food, traps: Optional[Trap], first_move: Tuple[int,int], depth: int = 3, start_time: float = 0.0) -> float:
        my_head = snake.get_head_position()[:]
        my_body = [seg[:] for seg in snake.segments]
        opp_head = opponent.get_head_position()[:] if opponent and opponent.alive else None
        opp_body = [seg[:] for seg in opponent.segments] if opponent and opponent.alive else []

        traps_set = set(tuple(t) for t in (traps.positions if traps and traps.positions else []))
        food_list = [tuple(f) for f in food.positions] if food and food.positions else []

        my_head, my_body = self._simulate_step(my_head, my_body, first_move)

        if not (0 <= my_head[0] < GRID_WIDTH and 0 <= my_head[1] < GRID_HEIGHT):
            return -1e9
        if tuple(my_head) in set(tuple(s) for s in my_body[1:]):
            return -1e9
        if opp_body and tuple(my_head) in set(tuple(s) for s in opp_body):
            return -1e9
        if tuple(my_head) in traps_set and snake.shield_timer <= 0:
            return -1e7

        def heuristic(my_h, my_b, opp_h, opp_b):
            food_dist = min((get_distance(my_h, f) for f in food_list), default=float('inf'))
            food_score = self.food_weight / (food_dist + 1.0)

            my_area = self._flood_fill_area(my_h, my_b, opp_b, self.max_bfs_nodes)
            opp_area = self._flood_fill_area(opp_h, opp_b, my_b, self.max_bfs_nodes) if opp_h else 0
            area_score = self.area_weight * (my_area - opp_area)

            trap_dist = min((get_distance(my_h, t) for t in traps_set), default=float('inf')) if traps_set else float('inf')
            trap_score = -self.trap_penalty / (trap_dist + 1.0) if trap_dist < 4 else 0

            len_diff = len(my_b) - (len(opp_b) if opp_b else 0)
            length_score = self.length_weight * math.tanh(len_diff / 3.0)

            astar_bonus = 0.0
            if food_list:
                try_targets = sorted(food_list, key=lambda p: get_distance(my_h, p))[:2]
                for t in try_targets:
                    path = self._astar(my_h, list(t), set(tuple(s) for s in my_b) | set(tuple(s) for s in opp_b) | traps_set, max_nodes=120)
                    if path:
                        astar_bonus = self.astar_bonus / (len(path))
                        break

            opp_pred = self._predict_opponent_next_heads(opponent, steps=3) if opponent else []
            min_opp_dist = min((get_distance(my_h, p) for p in opp_pred), default=float('inf'))
            danger_score = 0.0
            if min_opp_dist < 2:
                if opp_b and len(opp_b) >= len(my_b):
                    danger_score = -self.danger_weight * (2.0 - min_opp_dist)
                else:
                    danger_score = -self.danger_weight * 0.4 * (2.0 - min_opp_dist)

            total = food_score + area_score + astar_bonus + length_score + trap_score + danger_score
            return total

        def predict_opponent_moves(opp_h, opp_b, my_b):
            moves = self._available_moves_from(opp_h, opp_b, my_b)
            if not moves:
                return [ (0,0) ]
            scored = []
            for mv in moves:
                nxt = (opp_h[0] + mv[0], opp_h[1] + mv[1])
                dfood = min((get_distance(nxt, f) for f in food_list), default=float('inf'))
                scored.append( (dfood, mv) )
            scored.sort(key=lambda x: x[0])
            return [m for _,m in scored[:3]]

        def minimax(my_h, my_b, opp_h, opp_b, depth, alpha, beta, maximizing_player):
            if time.time() - start_time > self.time_budget:
                return heuristic(my_h, my_b, opp_h, opp_b)
            if depth == 0:
                return heuristic(my_h, my_b, opp_h, opp_b)

            if maximizing_player:
                val = -float('inf')
                moves = self._available_moves_from(my_h, my_b, opp_b)
                if not moves:
                    return -1e6
                for mv in moves:
                    nxt_h, nxt_b = self._simulate_step(my_h, my_b, mv)
                    if not (0 <= nxt_h[0] < GRID_WIDTH and 0 <= nxt_h[1] < GRID_HEIGHT):
                        continue
                    if tuple(nxt_h) in set(tuple(s) for s in nxt_b[1:]):
                        continue
                    if opp_b and tuple(nxt_h) in set(tuple(s) for s in opp_b):
                        continue
                    v = minimax(nxt_h, nxt_b, opp_h, opp_b, depth-1, alpha, beta, False)
                    val = max(val, v)
                    alpha = max(alpha, val)
                    if alpha >= beta:
                        break
                return val
            else:
                val = float('inf')
                if not opp_h:
                    return heuristic(my_h, my_b, opp_h, opp_b)
                moves = predict_opponent_moves(opp_h, opp_b, my_b)
                if not moves:
                    return heuristic(my_h, my_b, opp_h, opp_b)
                for mv in moves:
                    nxt_opp_h, nxt_opp_b = self._simulate_step(opp_h, opp_b, mv)
                    if not (0 <= nxt_opp_h[0] < GRID_WIDTH and 0 <= nxt_opp_h[1] < GRID_HEIGHT):
                        continue
                    if tuple(nxt_opp_h) in set(tuple(s) for s in nxt_opp_b[1:]):
                        continue
                    if tuple(nxt_opp_h) in set(tuple(s) for s in my_b):
                        v = -1e5
                    else:
                        v = minimax(my_h, my_b, nxt_opp_h, nxt_opp_b, depth-1, alpha, beta, True)
                    val = min(val, v)
                    beta = min(beta, val)
                    if alpha >= beta:
                        break
                return val

        try:
            score = minimax(tuple(my_head), my_body, tuple(opp_head) if opp_head else None, opp_body, depth, -float('inf'), float('inf'), True)
        except Exception:
            score = -1e6
        return score

    def get_possible_moves(self, snake: Snake) -> List[Tuple[int,int]]:
        cur = snake.direction if snake.direction is not None else Direction.RIGHT
        candidates = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        return [m for m in candidates if m != Direction.opposite(cur)]