import pygame
import random
import sys
import math

# Initialize pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
DARK_GREEN = (0, 200, 0)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 0)
DARK_YELLOW = (200, 200, 0)
WALL_COLOR = (100, 100, 255)  # Brighter wall color

# Game settings
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
SNAKE_SPEED = 10  # Grid cells per second
WALL_THICKNESS = 10  # Thicker walls

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Grid Snake Game')
clock = pygame.time.Clock()

# Font
font = pygame.font.SysFont('Arial', 25)
large_font = pygame.font.SysFont('Arial', 50)

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

    def reset(self, start_x, start_y):
        self.segments = []
        self.segments.append([start_x, start_y])
        self.direction = (1, 0)  # Right by default
        self.next_direction = (1, 0)
        self.speed = SNAKE_SPEED
        self.grow = 0
        self.length = 1
        self.alive = True
        self.score = 0
        self.move_timer = 0

    def get_head_position(self):
        return self.segments[0][:]

    def get_body_positions(self):
        return [segment[:] for segment in self.segments[1:]]

    def update(self, dt):
        if not self.alive:
            return False

        # Update tongue animation
        self.tongue_timer += dt
        if self.tongue_timer > 0.5:  # Every 0.5 seconds
            self.tongue_timer = 0
            self.tongue_length = 10 if random.random() > 0.7 else 0  # 30% chance to show tongue

        # Grid-based movement with timer
        self.move_timer += dt
        move_interval = 1.0 / self.speed
        
        if self.move_timer >= move_interval:
            self.move_timer = 0
            self.direction = self.next_direction
            
            # Calculate new head position
            head_x, head_y = self.segments[0]
            new_head = [
                (head_x + self.direction[0]) % GRID_WIDTH,
                (head_y + self.direction[1]) % GRID_HEIGHT
            ]
            
            # Check wall collision (no more wrapping)
            if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
                self.alive = False
                return False

            self.segments.insert(0, new_head)

            if self.grow > 0:
                self.grow -= 1
                self.length += 1
            else:
                self.segments.pop()

            # Check self collision
            for segment in self.segments[1:]:
                if new_head == segment:
                    self.alive = False
                    return False

        return True
    
    def check_collision_with_other(self, other_snake):
        if not self.segments or not other_snake.segments:
            return False
            
        head = self.segments[0]
        for segment in other_snake.segments:
            if head == segment:
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
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            ]
            is_colliding = False
            if snake_segments:
                for segment in snake_segments:
                    if position == [segment[0], segment[1]]:
                        is_colliding = True
                        break
            if not is_colliding and position not in self.positions:
                return position

    def spawn_multiple(self, snake_segments=None):
        self.positions = []
        for _ in range(self.num_foods):
            new_food_position = self.spawn(snake_segments)
            if new_food_position:
                self.positions.append(new_food_position)

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

def get_distance(pos1, pos2):
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

def is_safe(snake, new_head_pos, other_snake=None):
    # Check wall collision
    if not (0 <= new_head_pos[0] < GRID_WIDTH and 0 <= new_head_pos[1] < GRID_HEIGHT):
        return False
    # Check self-collision (excluding the neck)
    for segment in snake.segments[1:]:
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

def main():
    snake1 = Snake(GREEN, DARK_GREEN, GRID_WIDTH//4, GRID_HEIGHT//2, "Agent 1")
    snake2 = Snake(YELLOW, DARK_YELLOW, 3 * GRID_WIDTH//4, GRID_HEIGHT//2, "Agent 2")
    num_initial_foods = 10
    food = Food(num_initial_foods)

    running = True
    last_time = pygame.time.get_ticks()

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0  # Delta time in seconds
        last_time = current_time

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake1.change_direction((0, -1))
                elif event.key == pygame.K_DOWN:
                    snake1.change_direction((0, 1))
                elif event.key == pygame.K_LEFT:
                    snake1.change_direction((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    snake1.change_direction((1, 0))
                elif event.key == pygame.K_w:
                    snake2.change_direction((0, -1))
                elif event.key == pygame.K_s:
                    snake2.change_direction((0, 1))
                elif event.key == pygame.K_a:
                    snake2.change_direction((-1, 0))
                elif event.key == pygame.K_d:
                    snake2.change_direction((1, 0))
                elif event.key == pygame.K_SPACE and (not snake1.alive or not snake2.alive):
                    snake1.reset(GRID_WIDTH//4, GRID_HEIGHT//2)
                    snake2.reset(3 * GRID_WIDTH//4, GRID_HEIGHT//2)
                    food = Food(num_initial_foods)

        # Get AI agent decisions
        if snake1.alive:
            new_direction1 = agent_logic_player_1(snake1, food, snake2)
            snake1.change_direction(new_direction1)

        if snake2.alive:
            new_direction2 = agent_logic_player_2(snake2, food, snake1)
            snake2.change_direction(new_direction2)

        # Update game logic for snake 1
        if snake1.alive:
            if snake1.update(dt):
                # Check if snake 1 eats food
                if food.check_collision(snake1.get_head_position()):
                    snake1.grow = snake1.growth_amount
                    snake1.score += 1
                    # Spawn new food if below threshold
                    if len(food.positions) < num_initial_foods // 2:
                        food.spawn_multiple(snake1.segments + snake2.segments)
                # Check collision with snake 2
                if snake1.check_collision_with_other(snake2):
                    snake1.alive = False
                    print(f"{snake1.agent_id} collided with {snake2.agent_id} and died.")
            else:
                print(f"{snake1.agent_id} died with score: {snake1.score}")

        # Update game logic for snake 2
        if snake2.alive:
            if snake2.update(dt):
                # Check if snake 2 eats food
                if food.check_collision(snake2.get_head_position()):
                    snake2.grow = snake2.growth_amount
                    snake2.score += 1
                    # Spawn new food if below threshold
                    if len(food.positions) < num_initial_foods // 2:
                        food.spawn_multiple(snake1.segments + snake2.segments)
                # Check collision with snake 1
                if snake2.check_collision_with_other(snake1):
                    snake2.alive = False
                    print(f"{snake2.agent_id} collided with {snake1.agent_id} and died.")
            else:
                print(f"{snake2.agent_id} died with score: {snake2.score}")

        # Drawing
        screen.fill(BLACK)

        # Draw grid lines (optional)
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

        # Draw border/walls
        pygame.draw.rect(screen, WALL_COLOR, (0, 0, WIDTH, HEIGHT), WALL_THICKNESS)

        food.draw(screen)
        snake1.draw(screen)
        snake2.draw(screen)

        # Draw scores
        score_text_1 = font.render(f"{snake1.agent_id} Score: {snake1.score}", True, WHITE)
        screen.blit(score_text_1, (10, 10))
        score_text_2 = font.render(f"{snake2.agent_id} Score: {snake2.score}", True, WHITE)
        screen.blit(score_text_2, (10, 40))

        # Game over message
        if not snake1.alive or not snake2.alive:
            game_over_text = large_font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 60))
            restart_text = font.render("Press SPACE to restart", True, WHITE)
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()