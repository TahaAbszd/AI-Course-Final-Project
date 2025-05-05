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

# Game settings
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
SNAKE_SPEED = 100  # Pixels per second
TURN_RATE = 360  # Degrees per second for smooth turns

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('AI Snake Competition')
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
        self.growth_amount = 8
        self.tongue_timer = 0
        self.tongue_length = 0

    def reset(self, start_x, start_y):
        self.segments = []
        self.segments.append([start_x, start_y])
        self.direction = 0  # Angle in degrees (0 = right)
        self.target_direction = 0
        self.speed = SNAKE_SPEED
        self.grow = 0
        self.length = 1
        self.alive = True
        self.score = 0

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

        # Smooth turning
        angle_diff = (self.target_direction - self.direction + 180) % 360 - 180
        turn_amount = TURN_RATE * dt
        if abs(angle_diff) < turn_amount:
            self.direction = self.target_direction
        else:
            self.direction += turn_amount * (1 if angle_diff > 0 else -1)

        # Convert angle to direction vector
        rad = math.radians(self.direction)
        dx = math.cos(rad) * self.speed * dt
        dy = -math.sin(rad) * self.speed * dt

        # Update head position
        new_head = [self.segments[0][0] + dx, self.segments[0][1] + dy]
        self.segments.insert(0, new_head)

        if self.grow > 0:
            self.grow -= 1
            self.length += 1
        else:
            self.segments.pop()

        # Check wall collision
        head_x, head_y = self.segments[0]
        if (head_x < 0 or head_x > WIDTH or head_y < 0 or head_y > HEIGHT):
            self.alive = False
            return False

        # Check self collision (simplified)
        for segment in self.segments[10:]:  # Only check after neck
            if (abs(head_x - segment[0]) < GRID_SIZE/2 and
                abs(head_y - segment[1]) < GRID_SIZE/2):
                self.alive = False
                return False

        return True
    
    def check_collision_with_other(self, other_snake):
        head_x, head_y = self.get_head_position()
        for segment in other_snake.segments:
            if (abs(head_x - segment[0]) < GRID_SIZE / 2 and
                abs(head_y - segment[1]) < GRID_SIZE / 2):
                return True
        return False
    
    def change_direction(self, angle):
        self.target_direction = angle % 360

    def draw(self, surface):
        for i, segment in enumerate(self.segments):
            # Interpolate color from head to tail
            color_factor = i / self.length
            color = (
                int(self.color_primary[0] * (1 - color_factor) + self.color_secondary[0] * color_factor),
                int(self.color_primary[1] * (1 - color_factor) + self.color_secondary[1] * color_factor),
                int(self.color_primary[2] * (1 - color_factor) + self.color_secondary[2] * color_factor)
            )

            pygame.draw.circle(
                surface,
                color,
                (int(segment[0]), int(segment[1])),
                GRID_SIZE//2 - 2
            )

            # Draw pointy nose on head
            if i == 0:
                rad = math.radians(self.direction)
                nose_length = GRID_SIZE * 0.8

                # Calculate points for the head triangle
                center = (segment[0], segment[1])
                nose_tip = (
                    center[0] + math.cos(rad) * nose_length,
                    center[1] - math.sin(rad) * nose_length
                )

                # Points for the base of the triangle (wider than a circle)
                left_base = (
                    center[0] + math.cos(rad + math.pi/2) * GRID_SIZE//2,
                    center[1] - math.sin(rad + math.pi/2) * GRID_SIZE//2
                )
                right_base = (
                    center[0] + math.cos(rad - math.pi/2) * GRID_SIZE//2,
                    center[1] - math.sin(rad - math.pi/2) * GRID_SIZE//2
                )

                # Draw the head triangle
                pygame.draw.polygon(surface, color, [nose_tip, left_base, right_base])

                # Draw tongue if it's out
                if self.tongue_length > 0:
                    tongue_tip = (
                        nose_tip[0] + math.cos(rad) * self.tongue_length,
                        nose_tip[1] - math.sin(rad) * self.tongue_length
                    )
                    # Make the tongue wiggle
                    wiggle_angle = math.sin(self.tongue_timer * 20) * 0.3  # Wiggle factor
                    tongue_mid = (
                        nose_tip[0] + math.cos(rad + wiggle_angle) * self.tongue_length * 0.7,
                        nose_tip[1] - math.sin(rad + wiggle_angle) * self.tongue_length * 0.7
                    )

                    # Draw tongue as a curved line
                    pygame.draw.lines(
                        surface,
                        RED,
                        False,
                        [nose_tip, tongue_mid, tongue_tip],
                        3
                    )

                # Draw eyes on head
                eye_size = GRID_SIZE // 4
                pupil_size = eye_size // 2

                # Eye positions relative to direction
                for angle_offset in [math.pi/4, -math.pi/4]:  # Left and right eyes
                    # Eye white
                    eye_pos = (
                        segment[0] + math.cos(rad + angle_offset) * GRID_SIZE//3,
                        segment[1] - math.sin(rad + angle_offset) * GRID_SIZE//3
                    )
                    pygame.draw.circle(surface, WHITE, (int(eye_pos[0]), int(eye_pos[1])), eye_size)

                    # Eye outline for better visibility
                    pygame.draw.circle(surface, BLACK, (int(eye_pos[0]), int(eye_pos[1])), eye_size, 1)

                    # Pupil (positioned to look in the direction the snake is moving)
                    pupil_offset = GRID_SIZE // 8  # How much pupil is offset forward
                    pupil_pos = (
                        eye_pos[0] + math.cos(rad) * pupil_offset,
                        eye_pos[1] - math.sin(rad) * pupil_offset
                    )
                    pygame.draw.circle(surface, BLACK, (int(pupil_pos[0]), int(pupil_pos[1])), pupil_size)

                    # Optional: Add a small white highlight to make eyes more alive
                    highlight_pos = (
                        pupil_pos[0] + pupil_size//3,
                        pupil_pos[1] - pupil_size//3
                    )
                    pygame.draw.circle(surface, WHITE, (int(highlight_pos[0]), int(highlight_pos[1])), pupil_size//3)
class Food:
    def __init__(self, num_foods=1):
        self.num_foods = num_foods
        self.positions = []
        self.spawn_multiple()

    def spawn(self, snake_segments=None):
        while True:
            position = [
                random.randint(GRID_SIZE, WIDTH - GRID_SIZE),
                random.randint(GRID_SIZE, HEIGHT - GRID_SIZE)
            ]
            is_colliding = False
            if snake_segments:
                for segment in snake_segments:
                    if (abs(position[0] - segment[0]) < GRID_SIZE and
                        abs(position[1] - segment[1]) < GRID_SIZE):
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
            if (abs(head_position[0] - pos[0]) < GRID_SIZE and
                abs(head_position[1] - pos[1]) < GRID_SIZE):
                # Food eaten, remove it
                self.positions.pop(i)
                return True
        return False

    def draw(self, surface):
        for pos in self.positions:
            pygame.draw.circle(surface, RED, pos, GRID_SIZE//2 - 2)
            # Stem
            pygame.draw.rect(
                surface,
                DARK_GREEN,
                (pos[0] - 2, pos[1] - GRID_SIZE//2, 4, GRID_SIZE//4)
            )  
# --- AI Agent Logic Snippets ---


import math

def get_distance(pos1, pos2):
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

def get_angle_to_point(head_pos, target_pos):
    angle = math.degrees(math.atan2(head_pos[1] - target_pos[1], target_pos[0] - head_pos[0])) % 360
    return angle

def is_safe(snake, new_head_pos, other_snake=None):
    grid_size = 20  # Assuming GRID_SIZE is accessible here
    width = 800    # Assuming WIDTH is accessible here
    height = 600   # Assuming HEIGHT is accessible here

    # Check for wall collision
    if not (0 <= new_head_pos[0] < width and 0 <= new_head_pos[1] < height):
        return False
    # Check for self-collision (excluding the immediate neck)
    for i, segment in enumerate(snake.segments[:-1]): # Exclude the last segment as it will be removed
        if i < len(snake.segments) - 3: # Start checking after a few segments
            if get_distance(new_head_pos, segment) < grid_size * 0.6:
                return False
    # Check for collision with the other snake
    if other_snake:
        for segment in other_snake.segments:
            if get_distance(new_head_pos, segment) < grid_size * 0.6:
                return False
    return True

def agent_logic_player_1(snake, food, other_snake=None):
    head_pos = snake.get_head_position()
    current_direction = snake.direction
    grid_size = 20 # Assuming GRID_SIZE is accessible

    if not food.positions:
        return current_direction

    target_food = food.positions[0] # For simplicity, target the first food
    possible_moves = [current_direction, (current_direction + 90) % 360, (current_direction - 90) % 360]
    best_move = current_direction
    min_distance_to_food = get_distance(head_pos, target_food)

    for move in possible_moves:
        rad = math.radians(move)
        new_head_x = head_pos[0] + math.cos(rad) * grid_size
        new_head_y = head_pos[1] - math.sin(rad) * grid_size
        new_head_pos = [new_head_x, new_head_y]

        if is_safe(snake, new_head_pos, other_snake):
            distance_to_food = get_distance(new_head_pos, target_food)
            if distance_to_food < min_distance_to_food:
                min_distance_to_food = distance_to_food
                best_move = move

    return best_move

def agent_logic_player_2(snake, food, other_snake=None):
    head_pos = snake.get_head_position()
    current_direction = snake.direction
    grid_size = 20 # Assuming GRID_SIZE is accessible

    if not food.positions:
        return current_direction

    target_food = food.positions[0] # For simplicity, target the first food
    possible_moves = [current_direction, (current_direction + 90) % 360, (current_direction - 90) % 360]
    best_move = current_direction
    min_distance_to_food = get_distance(head_pos, target_food)

    for move in possible_moves:
        rad = math.radians(move)
        new_head_x = head_pos[0] + math.cos(rad) * grid_size
        new_head_y = head_pos[1] - math.sin(rad) * grid_size
        new_head_pos = [new_head_x, new_head_y]

        # Basic avoidance of the other snake
        avoidance_factor = 0
        if other_snake:
            distance_to_other = get_distance(head_pos, other_snake.get_head_position())
            angle_to_other = get_angle_to_point(head_pos, other_snake.get_head_position())
            angle_diff = (move - angle_to_other + 180) % 360 - 180
            if distance_to_other < 5 * grid_size:
                avoidance_factor = abs(angle_diff) # Penalize moves towards the other snake

        rad_move = math.radians(move)
        predicted_head_x = head_pos[0] + math.cos(rad_move) * grid_size
        predicted_head_y = head_pos[1] - math.sin(rad_move) * grid_size
        predicted_head_pos = [predicted_head_x, predicted_head_y]

        if is_safe(snake, predicted_head_pos, other_snake):
            distance_to_food = get_distance(predicted_head_pos, target_food) - avoidance_factor * 0.5 # Subtract to encourage avoidance
            if distance_to_food < min_distance_to_food:
                min_distance_to_food = distance_to_food
                best_move = move

    return best_move
# --- End of AI Agent Logic Snippets ---

def main():
    snake1 = Snake(GREEN, DARK_GREEN, WIDTH//4, HEIGHT//2, "Agent 1")
    snake2 = Snake(YELLOW, DARK_YELLOW, 3 * WIDTH//4, HEIGHT//2, "Agent 2")
    num_initial_foods = 10
    food = Food(num_initial_foods)

    running = True
    last_time = pygame.time.get_ticks()

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0  # Delta time in seconds
        last_time = current_time

        # Event handling (you might want to disable manual control for competition)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Optional: Allow manual override for testing
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    snake1.change_direction(90)
                elif event.key == pygame.K_s:
                    snake1.change_direction(270)
                elif event.key == pygame.K_a:
                    snake1.change_direction(180)
                elif event.key == pygame.K_d:
                    snake1.change_direction(0)
                elif event.key == pygame.K_UP:
                    snake2.change_direction(90)
                elif event.key == pygame.K_DOWN:
                    snake2.change_direction(270)
                elif event.key == pygame.K_LEFT:
                    snake2.change_direction(180)
                elif event.key == pygame.K_RIGHT:
                    snake2.change_direction(0)
                elif event.key == pygame.K_SPACE and (not snake1.alive or not snake2.alive):
                    snake1.reset(WIDTH//4, HEIGHT//2)
                    snake2.reset(3 * WIDTH//4, HEIGHT//2)
                    food = Food(num_initial_foods) # Reset food as well

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
                # Check collision with snake 1
                if snake2.check_collision_with_other(snake1):
                    snake2.alive = False
                    print(f"{snake2.agent_id} collided with {snake1.agent_id} and died.")
            else:
                print(f"{snake2.agent_id} died with score: {snake2.score}")

        # Check if all food is gone and respawn
        if not food.positions:
            food.spawn_multiple(snake1.segments + snake2.segments if snake1.alive or snake2.alive else None)

        # Drawing
        screen.fill(BLACK)

        # Draw border
        pygame.draw.rect(
            screen,
            BLUE,
            (0, 0, WIDTH, HEIGHT),
            GRID_SIZE//2
        )

        food.draw(screen)
        snake1.draw(screen)
        snake2.draw(screen)

        # Draw scores
        score_text_1 = font.render(f"{snake1.agent_id} Score: {snake1.score}", True, WHITE)
        screen.blit(score_text_1, (10, 10))
        score_text_2 = font.render(f"{snake2.agent_id} Score: {snake2.score}", True, WHITE)
        screen.blit(score_text_2, (10, 40))

        # Game over message
        game_over = not snake1.alive and not snake2.alive
        if not snake1.alive or not snake2.alive or game_over: # Include game_over flag
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