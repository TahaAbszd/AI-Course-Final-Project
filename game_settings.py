from dataclasses import dataclass
from enum import Enum, auto
import pygame
from typing import Tuple, List, Deque, Optional
from collections import deque
import random
import math

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
SNAKE_SPEED = 10
WALL_THICKNESS = 10

# Colors
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

class GameState(Enum):
    START = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    DRAW = auto()
    ROUND_OVER = auto()

@dataclass
class GameConfig:
    tournament_mode: bool = True
    max_rounds: int = 3                 # Number of round that snakes should be played for winning
    round_time: int = 55                # Time of Game
    trap_count: int = 15                # Number of traps in game
    trap_penalty: int = 2               # Points lost per trap hit
    trap_segment_penalty: int = 3       # Segments lost per trap hit
    head_collision_penalty: int = 4     # Points lost in head collisions 
    bodey_collision_penalty: int = 3    # Points lost in body collisions
    shield_duration: float = 2.0        # Shield Duration after each collisions
    collision_segment_penalty: int = 2  # Segments lost in any collision
    initial_food: int = 35              # Number of foods in game
    growth_per_food: int = 2            # Length growth of snakes per eating food
    min_snake_length: int = 5           # Minimum segments snake can have
    advantage_time: int = 5             # Seconds of advantage time after opponent dies
    

class Direction:
    RIGHT = (1, 0)
    LEFT = (-1, 0)
    UP = (0, -1)
    DOWN = (0, 1)

    @staticmethod
    def opposite(direction: Tuple[int, int]) -> Tuple[int, int]:
        return (-direction[0], -direction[1])

class GameObject:
    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

class Snake(GameObject):
    def __init__(self, color_primary: Tuple[int, int, int], 
                 color_secondary: Tuple[int, int, int], 
                 start_x: int, start_y: int, 
                 agent_id: str = "player"):
        self.color_primary = color_primary
        self.color_secondary = color_secondary
        self.agent_id = agent_id
        self.reset(start_x, start_y)
        self.config = GameConfig()
        
    def reset(self, start_x: int, start_y: int) -> None:
        self.segments: Deque[List[int]] = deque([[start_x, start_y]])
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.speed = SNAKE_SPEED
        self.grow = 0
        self.length = 1
        self.alive = True
        self.score = 0
        self.move_timer = 0
        self.shield_timer = 0
        self.shield_flash = 0
        self.self_collision = False

    def get_head_position(self) -> List[int]:
        return self.segments[0][:]

    def check_self_collision(self) -> bool:
        """Returns True if the snake collides with itself"""
        return self.segments.count(self.get_head_position()) > 1

    def get_body_positions(self) -> List[List[int]]:
        return [segment[:] for segment in self.segments[1:]]

    def update(self, dt:float) -> bool:
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
                    self.self_collision = True
                    return False
        return True
    
    def check_collision_with_other(self, other_snake: 'Snake') -> bool:
        if not self.segments or not other_snake.segments or self.shield_timer > 0 or other_snake.shield_timer > 0:
            return False

        head = self.segments[0]
        other_head = other_snake.segments[0]

        # Head-to-head collision
        if head == other_head:
            penalty = self.config.head_collision_penalty
            for _ in range(self.config.collision_segment_penalty):
                if self.score > other_snake.score:
                    other_snake.score = max(0, other_snake.score - penalty)
                    if len(other_snake.segments) > self.config.min_snake_length:
                        other_snake.segments.pop()
                        other_snake.length -= 1
                        
                    other_snake.shield_timer = self.config.shield_duration
                    
                elif other_snake.score > self.score:
                    self.score = max(0, self.score - penalty)
                    if len(self.segments) > self.config.min_snake_length:
                        self.segments.pop()
                        self.length -= 1
                    self.shield_timer = self.config.shield_duration
                    
                else:  # Equal scores - both get penalties
                    self.score = max(0, self.score - penalty)
                    other_snake.score = max(0, other_snake.score - penalty)
                    if len(self.segments) > self.config.min_snake_length:
                        self.segments.pop()
                        self.length -= 1
                        
                    if len(other_snake.segments) > self.config.min_snake_length:
                        other_snake.segments.pop()
                        other_snake.length -= 1

                    self.shield_timer = self.config.shield_duration
                    other_snake.shield_timer = self.config.shield_duration
                        
                return True

        # Body collision
        for segment in list(other_snake.segments)[1:]:
            if head == segment:
                for _ in range(self.config.collision_segment_penalty):  
                    self.score = max(0, self.score - self.config.body_collision_penalty)
                    if len(self.segments) > self.config.min_snake_length:
                        self.segments.pop()
                        self.length -= 1
                        
                    self.shield_timer = self.config.shield_duration

                return True
        return False
    
    def change_direction(self, new_dir: Tuple[int, int]) -> None:
        """preventing 180-degree turns"""
        if new_dir != Direction.opposite(self.direction):
            self.next_direction = new_dir

    def draw(self, surface: pygame.Surface) -> None:
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
    
    
    
class Food(GameObject):
    def __init__(self, num_foods: int = 1):
        self.num_foods = num_foods
        self.positions: List[Tuple[int, int]] = []

    def spawn(self, snake_segments: Optional[List[List[int]]] = None) -> Optional[Tuple[int, int]]:
        """Spawn a single food item in a valid position"""
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            position = (
                random.randint(1, GRID_WIDTH - 2),
                random.randint(1, GRID_HEIGHT - 2)
            )
            attempts += 1

            # Check if position is occupied by snake
            if snake_segments and any(position == (seg[0], seg[1]) for seg in snake_segments):
                continue

            # Check if position already has food
            if position not in self.positions:
                return position

        return None

    def spawn_multiple(self, num_foods: int, snake_segments: Optional[List[List[int]]] = None) -> None:
        """Spawn multiple food items"""
        self.positions = []
        for _ in range(num_foods):
            new_food = self.spawn(snake_segments)
            if new_food:
                self.positions.append(new_food)

    def check_collision(self, head_position: List[int]) -> bool:
        """Check if snake head collides with food"""
        for i, pos in enumerate(self.positions):
            if head_position == [pos[0], pos[1]]:
                self.positions.pop(i)
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all food items"""
        for pos in self.positions:
            pixel_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = pos[1] * GRID_SIZE + GRID_SIZE // 2

            # Draw apple
            pygame.draw.circle(
                surface, RED,
                (pixel_x, pixel_y),
                GRID_SIZE // 2 - 2
            )
            # Draw stem
            pygame.draw.rect(
                surface, DARK_GREEN,
                (pixel_x - 2, pixel_y - GRID_SIZE // 2, 4, GRID_SIZE // 4)
            )

class Trap(GameObject):
    def __init__(self, num_traps: int = 3):
        self.config = GameConfig()
        self.num_traps = num_traps
        self.positions: List[Tuple[int, int]] = []

    def spawn(self, 
          snake_segments: Optional[List[List[int]]] = None,
          food_positions: Optional[List[Tuple[int, int]]] = None) -> Optional[Tuple[int, int]]:
        """Spawn a single trap in a valid position"""
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            position = (
                random.randint(1, GRID_WIDTH - 2),
                random.randint(1, GRID_HEIGHT - 2)
            )
            attempts += 1

            # Check if position is occupied by snake
            if snake_segments and any(position == (seg[0], seg[1]) for seg in snake_segments):
                continue

            # Check if position has food
            if food_positions and position in food_positions:
                continue

            # Check if position already has a trap
            if position not in self.positions:
                return position

        return None

    def spawn_multiple(self, 
                  num_traps: int, 
                  snake_segments: Optional[List[List[int]]] = None,
                  food_positions: Optional[List[Tuple[int, int]]] = None) -> None:
        """Spawn multiple traps"""
        self.positions = []
        for _ in range(num_traps):
            new_trap = self.spawn(snake_segments, food_positions)
            if new_trap:
                self.positions.append(new_trap)

    def check_collision(self, snake: Snake) -> bool:
        """Check if snake collides with trap"""
        head = snake.get_head_position()
        for i, pos in enumerate(self.positions):
            if head == [pos[0], pos[1]]:
                # Apply more severe penalty to score
                snake.score = max(0, snake.score - (self.config.trap_penalty))  # Double penalty
                
                # Reduce length more aggressively (remove 2 segments if possible)
                for _ in range(self.config.trap_segment_penalty):
                    if len(snake.segments) > self.config.min_snake_length:
                        if snake.grow > 0:
                            snake.grow -= 1  # First reduce any pending growth
                        else:
                            snake.segments.pop()
                        snake.length -= 1
                
                # Activate shield
                snake.shield_timer = self.config.shield_duration
                
                # Remove the trap that was hit
                self.positions.pop(i)
                
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all traps"""
        for pos in self.positions:
            pixel_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = pos[1] * GRID_SIZE + GRID_SIZE // 2

            # Draw purple trap circle
            pygame.draw.circle(
                surface, PURPLE,
                (pixel_x, pixel_y),
                GRID_SIZE // 3
            )
            # Draw X mark
            pygame.draw.line(
                surface, BLACK,
                (pixel_x - GRID_SIZE // 4, pixel_y - GRID_SIZE // 4),
                (pixel_x + GRID_SIZE // 4, pixel_y + GRID_SIZE // 4),
                3
            )
            pygame.draw.line(
                surface, BLACK,
                (pixel_x + GRID_SIZE // 4, pixel_y - GRID_SIZE // 4),
                (pixel_x - GRID_SIZE // 4, pixel_y + GRID_SIZE // 4),
                3
            )

def get_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

def generate_spawn_positions() -> Tuple[Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]]:
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

def is_safe(snake: Snake, new_head_pos: List[int], other_snake: Optional[Snake] = None) -> bool:
    """
    Check if a position is safe for the snake to move to
    Args:
        snake: The snake moving
        new_head_pos: Proposed new head position
        other_snake: Optional other snake to check against
    Returns:
        bool: True if position is safe, False otherwise
    """
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

