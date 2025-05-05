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

# Game settings
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
SNAKE_SPEED = 100  # Pixels per second
TURN_RATE = 360  # Degrees per second for smooth turns

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Fluid Snake Game')
clock = pygame.time.Clock()

# Font
font = pygame.font.SysFont('Arial', 25)
large_font = pygame.font.SysFont('Arial', 50)

class Snake:
    def __init__(self):
        self.reset()
        self.growth_amount = 8
        self.tongue_timer = 0
        self.tongue_length = 0
        
    def reset(self):
        self.segments = []
        start_x, start_y = WIDTH//2, HEIGHT//2
        self.segments.append([start_x, start_y])
        self.direction = 0  # Angle in degrees (0 = right)
        self.target_direction = 0
        self.speed = SNAKE_SPEED
        self.grow = False
        self.length = 1
        
    def update(self, dt):
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
            return False
            
        # Check self collision (simplified)
        for segment in self.segments[10:]:  # Only check after neck
            if (abs(head_x - segment[0]) < GRID_SIZE/2 and 
                abs(head_y - segment[1]) < GRID_SIZE/2):
                return False
                
        return True
        
    def change_direction(self, angle):
        self.target_direction = angle
        
    def draw(self, surface):
        for i, segment in enumerate(self.segments):
            # Interpolate color from head to tail
            color_factor = i / self.length
            color = (
                int(GREEN[0] * (1 - color_factor) + DARK_GREEN[0] * color_factor),
                int(GREEN[1] * (1 - color_factor) + DARK_GREEN[1] * color_factor),
                int(GREEN[2] * (1 - color_factor) + DARK_GREEN[2] * color_factor)
            )
            
            pygame.draw.circle(
                surface, 
                color, 
                (int(segment[0]), int(segment[1])), 
                GRID_SIZE//2 - 2
            )
            
            # Draw pointy nose on head
            if i == 0:
                # Draw the head as a pointy shape
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
    def __init__(self):
        self.position = [0, 0]
        self.spawn()
        
    def spawn(self, snake_segments=None):
        while True:
            self.position = [
                random.randint(GRID_SIZE, WIDTH - GRID_SIZE),
                random.randint(GRID_SIZE, HEIGHT - GRID_SIZE)
            ]
            if snake_segments is None or not self.check_collision(snake_segments):
                break
                
    def check_collision(self, segments):
        for segment in segments:
            if (abs(self.position[0] - segment[0]) < GRID_SIZE and 
                abs(self.position[1] - segment[1]) < GRID_SIZE):
                return True
        return False
        
    def draw(self, surface):
        pygame.draw.circle(surface, RED, self.position, GRID_SIZE//2 - 2)
        # Stem
        pygame.draw.rect(
            surface, 
            DARK_GREEN, 
            (self.position[0] - 2, self.position[1] - GRID_SIZE//2, 4, GRID_SIZE//4)
        )

def main():
    snake = Snake()
    food = Food()
    score = 0
    
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
                    snake.change_direction(90)
                elif event.key == pygame.K_DOWN:
                    snake.change_direction(270)
                elif event.key == pygame.K_LEFT:
                    snake.change_direction(180)
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction(0)
                elif event.key == pygame.K_SPACE and not snake.alive:
                    snake.reset()
                    food.spawn()
                    score = 0
        
        # Game logic
        if snake.update(dt):
            # Check if snake eats food
            if (abs(snake.segments[0][0] - food.position[0]) < GRID_SIZE and 
                abs(snake.segments[0][1] - food.position[1]) < GRID_SIZE):
                snake.grow = snake.growth_amount  # Instead of True
                food.spawn(snake.segments)
                score += 1
        else:
            # Game over
            game_over_text = large_font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 30))
            restart_text = font.render("Press SPACE to restart", True, WHITE)
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 30))
            pygame.display.flip()
            
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        waiting = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        snake.reset()
                        food.spawn()
                        score = 0
                        waiting = False
                clock.tick(60)
            continue
        
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
        
        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()