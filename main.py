import pygame
import random
import sys
import time

# Initialize pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
DARK_GREEN = (0, 200, 0)
BLUE = (50, 50, 255)

# Game settings
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 25
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
SNAKE_SPEED = 12  # Frames per second
MOVE_DELAY = 100  # Milliseconds between moves

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Enhanced Snake Game')
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
        # Start position aligned to the grid
        self.segments = [[start_x // GRID_SIZE * GRID_SIZE, start_y // GRID_SIZE * GRID_SIZE]]
        self.direction = 0  # 0: Right, 1: Down, 2: Left, 3: Up
        self.next_direction = 0
        self.speed = SNAKE_SPEED  # Speed per grid cell per second (will be used differently now)
        self.move_timer = 0
        self.move_interval = 1.0 / (self.speed / GRID_SIZE) # Time to move one grid cell
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

        # Update tongue animation (remains the same)
        self.tongue_timer += dt
        if self.tongue_timer > 0.5:
            self.tongue_timer = 0
            self.tongue_length = 10 if random.random() > 0.7 else 0

        self.move_timer += dt
        if self.move_timer >= self.move_interval:
            self.move_timer -= self.move_interval
            self.direction = self.next_direction
            head_x, head_y = self.segments[0]
            new_head = list(self.segments[0])

            if self.direction == 0:  # Right
                new_head[0] += GRID_SIZE
            elif self.direction == 1:  # Down
                new_head[1] += GRID_SIZE
            elif self.direction == 2:  # Left
                new_head[0] -= GRID_SIZE
            elif self.direction == 3:  # Up
                new_head[1] -= GRID_SIZE

            self.segments.insert(0, new_head)
            if self.grow > 0:
                self.grow -= 1
                self.length += 1
            else:
                self.segments.pop()

            # Check wall collision
            head_x, head_y = self.segments[0]
            if not (0 <= head_x < WIDTH and 0 <= head_y < HEIGHT):
                self.alive = False
                return False

            # Check self collision
            for segment in self.segments[1:]:
                if self.segments[0] == segment:
                    self.alive = False
                    return False
            return True
        return True # Still alive, just hasn't moved a full grid cell yet

    def change_direction(self, direction):
        # Prevent immediate 180-degree turns
        if (self.direction == 0 and direction == 2) or \
           (self.direction == 2 and direction == 0) or \
           (self.direction == 1 and direction == 3) or \
           (self.direction == 3 and direction == 1):
            return
        self.next_direction = direction

    def draw(self, surface):
        for i, segment in enumerate(self.segments):
            color_factor = i / self.length
            color = (
                int(self.color_primary[0] * (1 - color_factor) + self.color_secondary[0] * color_factor),
                int(self.color_primary[1] * (1 - color_factor) + self.color_secondary[1] * color_factor),
                int(self.color_primary[2] * (1 - color_factor) + self.color_secondary[2] * color_factor)
            )
            pygame.draw.rect(surface, color, (segment[0], segment[1], GRID_SIZE, GRID_SIZE))

            # Draw head details (simplified for grid)
            if i == 0:
                center_x = segment[0] + GRID_SIZE // 2
                center_y = segment[1] + GRID_SIZE // 2
                eye_offset = GRID_SIZE // 4
                eye_size = GRID_SIZE // 8

                if self.direction == 0: # Right
                    pygame.draw.circle(surface, WHITE, (center_x + eye_offset, center_y - eye_offset), eye_size)
                    pygame.draw.circle(surface, WHITE, (center_x + eye_offset, center_y + eye_offset), eye_size)
                elif self.direction == 1: # Down
                    pygame.draw.circle(surface, WHITE, (center_x - eye_offset, center_y + eye_offset), eye_size)
                    pygame.draw.circle(surface, WHITE, (center_x + eye_offset, center_y + eye_offset), eye_size)
                elif self.direction == 2: # Left
                    pygame.draw.circle(surface, WHITE, (center_x - eye_offset, center_y - eye_offset), eye_size)
                    pygame.draw.circle(surface, WHITE, (center_x - eye_offset, center_y + eye_offset), eye_size)
                elif self.direction == 3: # Up
                    pygame.draw.circle(surface, WHITE, (center_x - eye_offset, center_y - eye_offset), eye_size)
                    pygame.draw.circle(surface, WHITE, (center_x + eye_offset, center_y - eye_offset), eye_size)
                    
class Food:
    def __init__(self):
        self.position = (0, 0)
        self.spawn()
        
    def spawn(self, snake_body=None):
        while True:
            self.position = (
                random.randint(0, GRID_WIDTH - 1), 
                random.randint(0, GRID_HEIGHT - 1)
            )
            if snake_body is None or self.position not in snake_body:
                break
                
    def draw(self, surface):
        center = (
            self.position[0] * GRID_SIZE + GRID_SIZE // 2,
            self.position[1] * GRID_SIZE + GRID_SIZE // 2
        )
        # Draw apple-like food
        pygame.draw.circle(surface, RED, center, GRID_SIZE // 2 - 2)
        # Stem
        pygame.draw.rect(
            surface, 
            DARK_GREEN, 
            (center[0] - 2, center[1] - GRID_SIZE//2, 4, GRID_SIZE//4)
        )

def draw_score(surface, score):
    score_text = font.render(f"Score: {score}", True, WHITE)
    surface.blit(score_text, (10, 10))

def game_over_screen(surface, score):
    surface.fill(BLACK)
    
    game_over_text = large_font.render("GAME OVER", True, RED)
    score_text = font.render(f"Final Score: {score}", True, WHITE)
    restart_text = font.render("Press SPACE to restart", True, WHITE)
    
    surface.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 60))
    surface.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    surface.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 60))
    
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def main():
    snake = Snake()
    food = Food()
    score = 0
    
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.change_direction((0, -1))
                elif event.key == pygame.K_DOWN:
                    snake.change_direction((0, 1))
                elif event.key == pygame.K_LEFT:
                    snake.change_direction((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction((1, 0))
        
        # Game logic
        if not snake.update(current_time):
            game_over_screen(screen, score)
            snake.reset()
            food.spawn()
            score = 0
            continue
            
        # Check if snake eats food
        if snake.body[0] == food.position:
            snake.grow = True
            food.spawn(snake.body)
            score += 1
        
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
        snake.draw(screen)
        draw_score(screen, score)
        
        pygame.display.update()
        clock.tick(SNAKE_SPEED)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()