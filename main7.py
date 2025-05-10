import pygame
import random
import sys
import copy
import math
from collections import deque

# --- Initialization ---
pygame.init()
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

SNAKE_SPEED = 10  # Grid cells per second
WALL_THICKNESS = 10  # Thicker walls

TOURNAMENT_MODE = True
MAX_ROUNDS = 3
ROUND_TIME = 120

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Tournament")
clock = pygame.time.Clock()

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 255, 50)
DARK_GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
DARK_YELLOW = (200, 200, 0)
RED = (255, 50, 50)
PURPLE = (150, 50, 200)
GRID_COLOR = (40, 40, 40)
WALL_COLOR = (50, 50, 100)
SHIELD_BLUE = (100, 100, 255)

# --- Fonts ---
font = pygame.font.SysFont('Arial', 24)
large_font = pygame.font.SysFont('Arial', 60, bold=True)
medium_font = pygame.font.SysFont('Arial', 36)

# --- Game States ---
START, PLAYING, GAME_OVER, DRAW, ROUND_OVER = "start", "playing", "game_over", "draw", "round_over"


class Snake:
    def __init__(self, color_primary, color_secondary, start_x, start_y, agent_id="player"):
        self.color_primary = color_primary
        self.color_secondary = color_secondary
        self.agent_id = agent_id
        self.reset(start_x, start_y)
        self.growth_amount = 3
        self.tongue_timer = 0
        self.tongue_length = 0
        self.direction = (1, 0)  # Right by default
        self.next_direction = (1, 0)
        self.shield_timer = 0
        self.shield_flash = 0

    def reset(self, start_x, start_y):
        self.segments = deque([[start_x, start_y]])
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.speed = SNAKE_SPEED
        self.grow = 0
        self.length = 1
        self.alive = True
        self.score = 0
        self.move_timer = 0
        self.shield_timer = 0

    def get_head_position(self):
        return self.segments[0][:]

    def get_body_positions(self):
        return [segment[:] for segment in self.segments[1:]]

    def update(self, dt):
        if not self.alive:
            return False

        # Update shield
        if self.shield_timer > 0:
            self.shield_timer -= dt
            self.shield_flash = (self.shield_flash + dt * 10) % 1

        # Movement
        self.move_timer += dt
        move_interval = 1.0 / self.speed
        
        if self.move_timer >= move_interval:
            self.move_timer = 0
            self.direction = self.next_direction
            
            head_x, head_y = self.segments[0]
            new_head = [
                head_x + self.direction[0],
                head_y + self.direction[1]
            ]
            
            # Wall collision
            if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
                self.alive = False
                return False

            self.segments.appendleft(new_head)

            if self.grow > 0:
                self.grow -= 1
                self.length += 1
            else:
                self.segments.pop()

            # Self collision
            for segment in list(self.segments)[1:]:
                if new_head == segment:
                    self.alive = False
                    return False

        return True
    
    def check_collision_with_other(self, other_snake):
        if not self.segments or not other_snake.segments or self.shield_timer > 0 or other_snake.shield_timer > 0:
            return False

        head = self.segments[0]
        other_head = other_snake.segments[0]

        # Head-to-head collision
        if head == other_head:
            if self.score > other_snake.score:
                other_snake.score = max(0, other_snake.score - 3)
                other_snake.length = max(3, other_snake.length - 1)
                other_snake.shield_timer = 2.0  # 2 seconds of immunity
                if other_snake.length < len(other_snake.segments):
                    other_snake.segments.pop()
            elif other_snake.score > self.score:
                self.score = max(0, self.score - 3)
                self.length = max(3, self.length - 1)
                self.shield_timer = 2.0
                if self.length < len(self.segments):
                    self.segments.pop()
            else:  # Equal scores -> both die
                self.alive = other_snake.alive = False
            return True

        # Body collision
        for segment in list(other_snake.segments)[1:]:
            if head == segment:
                self.alive = False
                return True
        return False
    
    def change_direction(self, new_dir):
        # Prevent 180-degree turns
        if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
            self.next_direction = new_dir

    def draw(self, surface):
        for i, segment in enumerate(self.segments):
            # Alternate body colors for a stripe pattern
            color = self.color_primary if i % 2 == 0 else self.color_secondary

            # Convert grid position to pixel position
            pixel_x = segment[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = segment[1] * GRID_SIZE + GRID_SIZE // 2

            if self.shield_timer > 0 and self.shield_flash < 0.5:
                shield_color = SHIELD_BLUE
                pygame.draw.circle(
                    surface, shield_color,
                    (pixel_x, pixel_y), 
                    GRID_SIZE//2 + 2, 2
                )
                
            # Draw body or head
            if i == 0:  # Head with pointy nose
                cx, cy = pixel_x, pixel_y
                half = GRID_SIZE // 2
                if self.direction == (1, 0):  # Right
                    points = [(cx + half, cy), (cx - half, cy - half), (cx - half, cy + half)]
                elif self.direction == (-1, 0):  # Left
                    points = [(cx - half, cy), (cx + half, cy - half), (cx + half, cy + half)]
                elif self.direction == (0, -1):  # Up
                    points = [(cx, cy - half), (cx - half, cy + half), (cx + half, cy + half)]
                else:  # Down
                    points = [(cx, cy + half), (cx - half, cy - half), (cx + half, cy - half)]

                pygame.draw.polygon(surface, self.color_primary, points)

                # Eyes
                eye_size = GRID_SIZE // 5
                pupil_size = eye_size // 2

                if self.direction == (1, 0):  # Right
                    left_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                    right_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y + GRID_SIZE//4)
                elif self.direction == (-1, 0):  # Left
                    left_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                    right_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y + GRID_SIZE//4)
                elif self.direction == (0, 1):  # Down
                    left_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                    right_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                else:  # Up
                    left_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y + GRID_SIZE//4)
                    right_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y + GRID_SIZE//4)

                pygame.draw.circle(surface, WHITE, left_eye_pos, eye_size)
                pygame.draw.circle(surface, WHITE, right_eye_pos, eye_size)
                pygame.draw.circle(surface, BLACK, left_eye_pos, pupil_size)
                pygame.draw.circle(surface, BLACK, right_eye_pos, pupil_size)
            else:
                # Body
                pygame.draw.rect(
                    surface,
                    color,
                    (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                )


class Food:
    def __init__(self, num_foods=1):
        self.num_foods = num_foods
        self.positions = []
        self.spawn_multiple()

    def spawn(self, snake_segments=None):
        while True:
            position = [
                random.randint(1, GRID_WIDTH - 2),
                random.randint(1, GRID_HEIGHT - 2)
            ]
            if snake_segments and any(position == [s[0], s[1]] for s in snake_segments):
                continue
            if position not in self.positions:
                return position

    def spawn_multiple(self, snake_segments=None):
        self.positions = []
        for _ in range(self.num_foods):
            pos = self.spawn(snake_segments)
            if pos:
                self.positions.append(pos)

    def check_collision(self, head_position):
        for i, pos in enumerate(self.positions):
            if head_position == [pos[0], pos[1]]:
                # Food eaten, remove it
                self.positions.pop(i)
                return True
        return False

    def draw(self, surface):
        for pos in self.positions:
            pixel_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = pos[1] * GRID_SIZE + GRID_SIZE // 2
            
            pygame.draw.circle(
                surface, 
                RED, 
                (pixel_x, pixel_y), 
                GRID_SIZE//2 - 2
            )
            # Stem
            pygame.draw.rect(
                surface,
                DARK_GREEN,
                (pixel_x - 2, pixel_y - GRID_SIZE//2, 4, GRID_SIZE//4)
            )
            
class Trap:
    def __init__(self, num_traps=3):
        self.num_traps = num_traps
        self.positions = []
        self.penalty = 2
        self.spawn_multiple()

    def spawn(self, snake_segments=None):
        while True:
            position = [
                random.randint(1, GRID_WIDTH - 2),
                random.randint(1, GRID_HEIGHT - 2)
            ]
            if snake_segments and any(position == [s[0], s[1]] for s in snake_segments):
                continue
            if position not in self.positions:
                return position

    def spawn_multiple(self, snake_segments=None):
        self.positions = []
        for _ in range(self.num_traps):
            pos = self.spawn(snake_segments)
            if pos:
                self.positions.append(pos)

    def check_collision(self, snake):
        head = snake.get_head_position()
        for i, pos in enumerate(self.positions):
            if head == [pos[0], pos[1]]:
                snake.score = max(0, snake.score - self.penalty)
                if snake.length > 3:
                    snake.segments.pop()
                    snake.length -= 1
                return True
        return False

    def draw(self, surface):
        for pos in self.positions:
            pixel_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = pos[1] * GRID_SIZE + GRID_SIZE // 2
            pygame.draw.circle(
                surface, PURPLE,
                (pixel_x, pixel_y), 
                GRID_SIZE//3
            )
            pygame.draw.line(
                surface, BLACK,
                (pixel_x - GRID_SIZE//4, pixel_y - GRID_SIZE//4),
                (pixel_x + GRID_SIZE//4, pixel_y + GRID_SIZE//4),
                3
            )
            pygame.draw.line(
                surface, BLACK,
                (pixel_x + GRID_SIZE//4, pixel_y - GRID_SIZE//4),
                (pixel_x - GRID_SIZE//4, pixel_y + GRID_SIZE//4),
                3
            )

            
        
def check_collision_with_other(self, other_snake):
    if not self.segments or not other_snake.segments:
        return False
        
    head = self.segments[0]
    if head == other_snake.segments[0]:  # Head-to-head
        if self.score > other_snake.score:
            other_snake.score = max(0, other_snake.score - 3)
            other_snake.shield_timer = 3.0  # 3-second shield
        elif other_snake.score > self.score:
            self.score = max(0, self.score - 3)
            self.shield_timer = 3.0
        else:  # Equal scores -> both die
            self.alive = other_snake.alive = False
        return True
    return False    

def get_distance(pos1, pos2):
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

def is_safe(snake, new_head_pos, other_snake=None):
    # Check wall collision
    if not (0 <= new_head_pos[0] < GRID_WIDTH and 0 <= new_head_pos[1] < GRID_HEIGHT):
        return False
    # Check self-collision (excluding the neck)
    for segment in list(snake.segments)[1:]:
        if new_head_pos == segment:
            return False
    # Check collision with other snake
    if other_snake:
        for segment in other_snake.segments:
            if new_head_pos == segment:
                return False
    return True

def agent_logic_player_1(snake, food, other_snake=None):
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
        if not is_safe(snake, new_head, other_snake):
            continue

        # Calculate food proximity score
        food_dist = get_distance(new_head, closest_food)
        food_score = 1 / (food_dist + 1e-5) * 100  # Avoid division by zero

        # Calculate mobility score
        mobility = 0
        next_moves = [m for m in [(1,0), (-1,0), (0,1), (0,-1)] if m != (-move[0], -move[1])]
        for next_move in next_moves:
            next_head_pos = [new_head[0] + next_move[0], new_head[1] + next_move[1]]
            if is_safe(snake, next_head_pos, other_snake):
                mobility += 1

        # Calculate danger score
        danger = 0
        if other_snake and other_snake.alive:
            other_head = other_snake.get_head_position()
            dist_to_other = get_distance(new_head, other_head)
            if dist_to_other < 4 and len(other_snake.segments) >= len(snake.segments):
                danger = 1
                # Predict other snake's movement
                other_dir = other_snake.direction
                predicted_other_head = [other_head[0] + other_dir[0], other_head[1] + other_dir[1]]
                if new_head == predicted_other_head:
                    danger += 1

        total_score = food_score + mobility * 15 - danger * 100
        if total_score > best_score:
            best_score = total_score
            best_move = move

    return best_move

def agent_logic_player_2(snake, food, other_snake=None):
    head_pos = snake.get_head_position()
    current_dir = snake.direction

    if not food.positions:
        return current_dir

    # Find safest food considering other snake
    food_scores = []
    for f in food.positions:
        base_score = 1 / (get_distance(head_pos, f) + 1e-5)
        # Penalize food close to other snake
        if other_snake:
            other_dist = get_distance(f, other_snake.get_head_position())
            base_score *= max(0.1, 1 - (1 / (other_dist + 1)))
        food_scores.append(base_score)
    target_food = food.positions[food_scores.index(max(food_scores))]

    possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    possible_moves = [move for move in possible_moves if move != (-current_dir[0], -current_dir[1])]

    best_move = current_dir
    best_score = -float('inf')

    for move in possible_moves:
        new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
        if not is_safe(snake, new_head, other_snake):
            continue

        # Food proximity
        food_dist = get_distance(new_head, target_food)
        food_score = 1 / (food_dist + 1e-5) * 100

        # Mobility
        mobility = 0
        next_moves = [m for m in [(1,0), (-1,0), (0,1), (0,-1)] if m != (-move[0], -move[1])]
        for next_move in next_moves:
            next_head_pos = [new_head[0] + next_move[0], new_head[1] + next_move[1]]
            if is_safe(snake, next_head_pos, other_snake):
                mobility += 1

        # Advanced danger detection
        danger = 0
        if other_snake and other_snake.alive:
            # Check if other snake is targeting same area
            other_path = []
            temp_head = other_snake.get_head_position()
            for _ in range(3):  # Predict next 3 moves
                temp_head = [temp_head[0] + other_snake.direction[0], 
                            temp_head[1] + other_snake.direction[1]]
                other_path.append(temp_head)
            if new_head in other_path:
                danger += 2

            # Space around other snake
            other_space = 0
            for m in [(1,0), (-1,0), (0,1), (0,-1)]:
                check_pos = [temp_head[0] + m[0], temp_head[1] + m[1]]
                if is_safe(other_snake, check_pos, snake):
                    other_space += 1
            if other_space <= 1:  # Other snake in tight space
                danger -= 1  # Less dangerous

        total_score = food_score + mobility * 20 - danger * 150
        if total_score > best_score:
            best_score = total_score
            best_move = move

    return best_move

# --- Random spawn positions and fruits ---
def generate_spawn_and_fruit_layout():
    s1 = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
    s2 = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
    while get_distance(s1, s2) < 5:  # Ensure snakes spawn apart
        s2 = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
    
    fruit_positions = []
    while len(fruit_positions) < 30:
        pos = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
        if pos not in fruit_positions and pos != s1 and pos != s2:
            fruit_positions.append(pos)
    return s1, s2, fruit_positions


def draw_scores(surface, snake1_wins, snake2_wins, snake1_score=None, snake2_score=None, time_left=None):
    if snake1_score is not None and snake2_score is not None:
        score1_text = f"Agent 1: Wins {snake1_wins} | Fruits: {snake1_score}"
        score2_text = f"Agent 2: Wins {snake2_wins} | Fruits: {snake2_score}"
    else:
        score1_text = f"Agent 1: {snake1_wins}"
        score2_text = f"Agent 2: {snake2_wins}"
    
    score1 = font.render(score1_text, True, GREEN)
    score2 = font.render(score2_text, True, YELLOW)
    surface.blit(score1, (10, 10))
    surface.blit(score2, (WIDTH - score2.get_width() - 10, 10))

    if time_left is not None:
        time_text = font.render(f"Time: {int(time_left)}s", True, WHITE)
        surface.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 10))

def draw_start_screen():
    screen.fill(BLACK)
    title = large_font.render("Snake Tournament", True, GREEN)
    instruction = medium_font.render("Press SPACE to begin", True, WHITE)
    controls = font.render("Agent 1: WASD | Agent 2: Arrow Keys", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
    screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2))
    screen.blit(controls, (WIDTH//2 - controls.get_width()//2, HEIGHT//2 + 50))


def draw_round_over_screen(round_winner, snake1_wins, snake2_wins, snake1_score, snake2_score, round_num):
    screen.fill(BLACK)
    title = large_font.render(f"Round {round_num} Over", True, WHITE)
    if round_winner:
        result = medium_font.render(f"{round_winner} wins!", True, GREEN if round_winner == "Agent 1" else YELLOW)
    else:
        result = medium_font.render("Draw!", True, YELLOW)
    fruits_text = font.render(f"Agent 1: {snake1_score} fruits | Agent 2: {snake2_score} fruits", True, WHITE)
    instruction = font.render("Press SPACE to continue", True, WHITE)
    
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
    screen.blit(result, (WIDTH//2 - result.get_width()//2, HEIGHT//2 - 50))
    screen.blit(fruits_text, (WIDTH//2 - fruits_text.get_width()//2, HEIGHT//2))
    screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 50))
    draw_scores(screen, snake1_wins, snake2_wins)


def draw_game_over_screen(winner, snake1_wins, snake2_wins):
    screen.fill(BLACK)
    title = large_font.render("Tournament Over", True, RED)
    result_text = medium_font.render(f"{winner} Wins!", True, GREEN if winner == "Agent 1" else YELLOW)
    score_text = font.render(f"Final Score: {snake1_wins}-{snake2_wins}", True, WHITE)
    instruction = font.render("Press SPACE to play again", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
    screen.blit(result_text, (WIDTH//2 - result_text.get_width()//2, HEIGHT//2 - 50))
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 50))
    
    
def draw_draw_screen(snake1_wins, snake2_wins):
    screen.fill(BLACK)
    title = large_font.render("Tournament Draw!", True, YELLOW)
    score_text = font.render(f"Final Score: {snake1_wins}-{snake2_wins}", True, WHITE)
    instruction = font.render("Press SPACE to play again", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 50))
    
    
def main():
    global game_state, current_round, snake1_wins, snake2_wins, round_winner

    # Tournament variables
    game_state = START
    current_round = 1
    snake1_wins = 0
    snake2_wins = 0
    round_winner = None
    round_start_time = 0
    losers_bracket = []
    rematches = []

    spawn1, spawn2, layout = generate_spawn_and_fruit_layout()

    def init_round(rnd, swap_positions=False):
        nonlocal spawn1, spawn2
        if swap_positions:
            spawn1, spawn2 = spawn2, spawn1
        s1 = Snake(GREEN, DARK_GREEN, *spawn1, "Agent 1")
        s2 = Snake(YELLOW, DARK_YELLOW, *spawn2, "Agent 2")
        f = Food(0)
        t = Trap(3)  
        f.positions = copy.deepcopy(layout)
        return s1, s2, f, t

    snake1, snake2, food, traps = init_round(current_round)
    last_time = pygame.time.get_ticks()

    while True:
        dt = (pygame.time.get_ticks() - last_time) / 1000.0
        last_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if game_state in [START, GAME_OVER, DRAW]:
                    game_state = PLAYING
                    current_round = 1
                    snake1_wins = 0
                    snake2_wins = 0
                    spawn1, spawn2, layout = generate_spawn_and_fruit_layout()
                    snake1, snake2, food, traps = init_round(current_round)
                    round_start_time = last_time / 1000.0
                    
                elif game_state == ROUND_OVER:
                    current_round += 1
                    snake1, snake2, food, traps = init_round(current_round, True)
                    game_state = PLAYING
                    round_start_time = last_time / 1000.0

        losers_bracket = []
        if game_state == ROUND_OVER and not round_winner:
            losers_bracket.append(snake1 if snake1.score < snake2.score else snake2)

        if game_state == START:
            draw_start_screen()

        elif game_state == PLAYING:
            elapsed_time = last_time / 1000.0 - round_start_time
            time_left = max(0, ROUND_TIME - elapsed_time)
    
            # Update snakes
            snake1_alive = snake1.alive
            snake2_alive = snake2.alive
            
            if snake1.alive:
                snake1.change_direction(agent_logic_player_1(snake1, food, snake2))
                snake1_alive = snake1.update(dt)
                if snake1_alive and food.check_collision(snake1.get_head_position()):
                    snake1.grow += 3
                    snake1.score += 1

            if snake2.alive:
                snake2.change_direction(agent_logic_player_2(snake2, food, snake1))
                snake2_alive = snake2.update(dt)
                if snake2_alive and food.check_collision(snake2.get_head_position()):
                    snake2.grow += 3
                    snake2.score += 1

            if snake1.alive:
                traps.check_collision(snake1)
            if snake2.alive:
                traps.check_collision(snake2)
                
            if snake1.alive and snake2.alive:
                snake1.check_collision_with_other(snake2)
                snake2.check_collision_with_other(snake1)
                    
            
            # Check round end conditions
            round_over = False
            if time_left <= 0 or (not snake1.alive and not snake2.alive) or len(food.positions) == 0:
                round_over = True
            
            if round_over:
                # Determine round winner
                if snake1.score > snake2.score:
                    round_winner = "Agent 1"
                    snake1_wins += 1
                elif snake2.score > snake1.score:
                    round_winner = "Agent 2"
                    snake2_wins += 1
                else:
                    round_winner = None
                    if TOURNAMENT_MODE:
                        losers_bracket.append((snake1, snake2, food, traps))
                            
            # Check tournament progression
                if TOURNAMENT_MODE:
                    if current_round >= MAX_ROUNDS:
                        if snake1_wins == snake2_wins and len(losers_bracket) > 0:
                            # Play tiebreaker from losers bracket
                            rematches = losers_bracket.copy()
                            losers_bracket = []
                            current_round = 1
                            snake1, snake2, food, traps = rematches.pop()
                            round_start_time = last_time / 1000.0
                        else:
                            # Tournament over
                            if snake1_wins > snake2_wins:
                                game_state = GAME_OVER
                                final_winner = "Agent 1"
                            elif snake2_wins > snake1_wins:
                                game_state = GAME_OVER
                                final_winner = "Agent 2"
                            else:
                                game_state = DRAW
                    else:
                        game_state = ROUND_OVER
                else:
                    game_state = ROUND_OVER

            # Draw everything
            screen.fill(BLACK)
            # Draw grid
            for x in range(0, WIDTH, GRID_SIZE):
                pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
            for y in range(0, HEIGHT, GRID_SIZE):
                pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))
            pygame.draw.rect(screen, WALL_COLOR, (0, 0, WIDTH, HEIGHT), WALL_THICKNESS)
            
            # Draw game elements
            food.draw(screen)
            traps.draw(screen)
            snake1.draw(screen)
            snake2.draw(screen)
            draw_scores(screen, snake1_wins, snake2_wins, snake1.score, snake2.score, time_left)

        elif game_state == ROUND_OVER:
            draw_round_over_screen(
                round_winner, snake1_wins, snake2_wins, 
                snake1.score, snake2.score, current_round
            )

        elif game_state == GAME_OVER:
            draw_game_over_screen(final_winner, snake1_wins, snake2_wins)

        elif game_state == DRAW:
            draw_draw_screen(snake1_wins, snake2_wins)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()