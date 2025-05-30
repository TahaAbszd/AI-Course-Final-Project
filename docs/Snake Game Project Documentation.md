# Snake Game Project Documentation

## 1\. Introduction

This document outlines the design, mechanics, and structure of the Snake Game project. It's a 2-player (or Player vs. AI, AI vs. AI) version of the classic Snake game, built using Python and the Pygame library. The game features multiple AI bot strategies, a tournament mode, various game elements like traps, and configurable game settings.

## 2\. Core Game Mechanics

The game revolves around controlling a snake to eat food, grow longer, and achieve a higher score than the opponent, all while avoiding hazards.

* **Objective:**  
  * Grow your snake by eating food.  
  * Score points for each food item consumed.  
  * Outlive your opponent or have a higher score when the round ends.  
  * Win the majority of rounds in a tournament.  
* **Snakes:**  
  * **Movement:** Snakes move at a constant speed on a grid. Players/bots can change the snake's direction (Up, Down, Left, Right), but cannot immediately reverse into their own body.  
  * **Growth:** Eating food increases the snake's length by a configured number of segments (growth\_per\_food).  
  * **Collision:**  
    * **Self-Collision:** If a snake's head collides with its own body, it dies (or enters an "advantage time" for the opponent).  
    * **Wall Collision:** Colliding with the game boundaries results in death.  
    * **Opponent Collision:**  
      * **Head-to-Head:** Both snakes may receive penalties (lose segments, score reduction) and a temporary shield. The outcome can depend on relative scores.  
      * **Head-to-Body:** The snake whose head hits an opponent's body receives penalties and a shield.  
* **Food:**  
  * Appears at random unoccupied locations on the grid.  
  * When eaten, it disappears, increases the consumer's score and length, and a new food item may spawn elsewhere.  
* **Traps:**  
  * Appear at random unoccupied locations (avoiding food and snakes initially).  
  * If a snake's head hits a trap:  
    * The snake loses score points (trap\_penalty).  
    * The snake loses segments (trap\_segment\_penalty).  
    * The snake gains a temporary shield.  
    * The trap disappears.  
* **Walls:**  
  * The game area is enclosed by walls. Hitting a wall means the snake dies and is out for the current round.  
* **Scoring:**  
  * Primarily by eating food (+1 point per food, or as configured).  
  * Penalties for hitting traps or colliding with opponents reduce the score.  
  * Minimum snake length is enforced.  
* **Rounds & Timers:**  
  * A game (tournament match) consists of multiple rounds (max\_rounds).  
  * Each round has a time limit (round\_time).  
  * A round ends if:  
    * Time runs out.  
    * Both snakes die.  
    * All food is eaten (if this is a defined win condition, though currently it ends the round).  
  * The winner of a round is the snake that is alive at the end, or if both are alive, the one with the higher score. If scores are equal, it's a draw for the round.  
* **Tournament Mode:**  
  * The game is structured as a tournament between two agents (bots or a player).  
  * Wins, losses, and scores are tracked across rounds.  
  * The agent winning the most rounds wins the tournament. Tie-breaking rules (like total score or extra rounds) can apply.  
  * **Advantage Time:** If one snake dies due to self-collision or wall collision, the other snake gets a period of "advantage time" (advantage\_time). If the surviving snake also dies during this period, it may affect the round outcome. If it survives, it solidifies its win for that scenario.  
  * **Early Victory:** A significant point difference (early\_victory\_diff) after a minimum number of rounds (min\_rounds\_for\_early\_victory) can result in an early tournament win.  
* **Shield Mechanic:**  
  * After certain collisions (head-to-head, head-to-body with opponent, or hitting a trap), a snake receives a temporary shield (shield\_duration).  
  * While shielded, the snake is typically immune to further collision penalties with other snakes.  
  * Visually indicated by a flashing effect.

## 3\. Project File Structure

The project is organized into several Python files:

* **game\_settings.py:** Defines all core game entities (Snake, Food, Trap), game constants (screen dimensions, grid size, colors), the GameConfig dataclass for game rules, the GameState enum, and utility functions like get\_distance and is\_safe.  
* **bot.py:** Contains the base Bot class and specific AI implementations (RandomBot, GreedyBot, StrategicBot, CustomBot, UserBot). This is where agent decision-making logic resides.  
* **main.py (or equivalent, e.g., snake\_game.py):** The main script that initializes Pygame, runs the game loop, manages game states, handles user input, renders graphics, and integrates the bots and tournament logic. It contains the SnakeGame class.  
* **tournament.py (inferred):** This file (not provided but used by SnakeGame) is responsible for managing the logic of a tournament: tracking round results, scores, wins, determining the overall winner, and saving tournament statistics.

## 4\. Key Classes and Their Logic

### 4.1. From game\_settings.py

* **Direction Class**  
  * **Purpose:** Provides named constants for movement vectors (tuples like (dx, dy)) and a utility to find the opposite direction. Enhances code readability.  
  * **Key Attributes:** RIGHT \= (1, 0\), LEFT \= (-1, 0\), UP \= (0, \-1), DOWN \= (0, 1\).  
  * **Key Methods:** opposite(direction): Returns the inverse of a given direction tuple.  
* **GameState Enum**  
  * **Purpose:** Defines distinct states the game can be in, controlling the main game loop's behavior.  
  * **Values:** START, PLAYING, GAME\_OVER, DRAW, ROUND\_OVER.  
* **GameConfig Dataclass**  
  * **Purpose:** A centralized container for all configurable game parameters, making it easy to tweak game rules and behavior.  
  * **Key Attributes:** tournament\_mode, max\_rounds, round\_time, trap\_count, trap\_penalty, shield\_duration, initial\_food, growth\_per\_food, min\_snake\_length, early\_victory\_diff, etc.  
* **GameObject Class**  
  * **Purpose:** An abstract base class for any object in the game that needs to be drawn on the screen.  
  * **Key Methods:** draw(surface): Abstract method to be implemented by subclasses for rendering.  
* **Snake Class (inherits GameObject)**  
  * **Purpose:** Represents a snake, managing its segments, movement, state, score, and interactions.  
  * **Key Attributes:**  
    * segments: A deque of \[x,y\] coordinates representing the snake's body, head at index 0\.  
    * direction: Current actual direction of movement (a tuple like (1,0)).  
    * next\_direction: Buffered direction for the next move tick.  
    * score: The snake's current score.  
    * alive: Boolean indicating if the snake is currently alive.  
    * shield\_timer: Countdown for how long the shield remains active.  
    * agent\_id: Name of the bot/player controlling this snake.  
    * config: An instance of GameConfig.  
  * **Key Methods:**  
    * reset(start\_x, start\_y): Initializes/resets the snake to a starting state.  
    * update(dt): Handles movement logic per frame, including moving segments, growing, and checking for self-collision or wall collision. dt is delta time.  
    * change\_direction(new\_dir): Sets next\_direction if new\_dir isn't opposite to current direction.  
    * check\_collision\_with\_other(other\_snake): Manages logic for head-to-head and head-to-body collisions with another snake, applying penalties and shields.  
    * get\_head\_position(): Returns a copy of the head's \[x,y\] coordinates.  
    * draw(surface): Renders the snake (head with eyes, body segments, shield effect).  
* **Food Class (inherits GameObject)**  
  * **Purpose:** Manages food items in the game.  
  * **Key Attributes:** positions: A list of (x,y) tuples for all active food items.  
  * **Key Methods:**  
    * spawn\_multiple(num\_foods, snake\_segments): Spawns a specified number of food items in valid locations.  
    * check\_collision(head\_position): Checks if a snake's head has collided with any food; if so, removes the food.  
    * draw(surface): Renders all food items.  
* **Trap Class (inherits GameObject)**  
  * **Purpose:** Manages traps in the game.  
  * **Key Attributes:** positions: A list of (x,y) tuples for all active traps. config: An instance of GameConfig.  
  * **Key Methods:**  
    * spawn\_multiple(num\_traps, snake\_segments, food\_positions): Spawns traps in valid locations.  
    * check\_collision(snake): Checks if a given snake has collided with a trap; if so, applies penalties and shield to the snake and removes the trap.  
    * draw(surface): Renders all traps.

### 4.2. From bot.py

* **Bot Class (Base)**  
  * **Purpose:** An abstract base class defining the interface for all AI agents.  
  * **Key Attributes:** name (string identifier), config (dictionary for bot-specific weights/parameters).  
  * **Key Methods:** decide\_move(snake, food, opponent): Abstract method. Subclasses must implement this to return a direction tuple (dx, dy) representing the chosen move.  
* **RandomBot Class (inherits Bot)**  
  * **Logic:** Chooses a random valid direction (not opposite to current movement).  
* **GreedyBot Class (inherits Bot)**  
  * **Logic:** Primarily aims for the nearest food. Includes basic safety checks (avoiding walls, self, opponent) and a simple mobility score to avoid getting trapped.  
* **StrategicBot Class (inherits Bot)**  
  * **Logic:** A more advanced bot that considers:  
    * Safer food choices (e.g., food further from the opponent).  
    * Predicting the opponent's next few moves to avoid collisions or contest areas.  
    * Mobility and available space.  
    * Advanced danger detection.

### 4.3. From main.py (or equivalent)

* **SnakeGame Class**  
  * **Purpose:** The main class that initializes Pygame, manages the game window, orchestrates the game loop, handles events, updates game states, and renders all visual elements.  
  * **Key Attributes:**  
    * screen: The Pygame display surface.  
    * clock: Pygame clock for managing frame rate.  
    * game\_state: Current state of the game (instance of GameState).  
    * config: An instance of GameConfig.  
    * snake1, snake2: Instances of the Snake class.  
    * food: Instance of the Food class.  
    * traps: Instance of the Trap class.  
    * bot1, bot2: Instances of Bot subclasses.  
    * tournament: Instance of the Tournament class.  
    * round\_start\_time, snake1\_advantage\_time, etc.: Timers for round and advantage logic.  
  * **Key Methods:**  
    * run(): Contains the main game loop.  
    * handle\_events(): Processes Pygame events (keyboard input, quit).  
    * update(): Updates the game logic each frame based on the current game\_state. This includes getting moves from bots, updating snakes, checking collisions, and managing round timers/conditions.  
    * draw(): Renders the current game scene based on game\_state (e.g., start screen, playing field, round over screen).  
    * reset\_round(swap\_positions): Initializes snakes, food, and traps for a new round.  
    * check\_collisions(): Centralized method to check food, trap, and snake-on-snake collisions.  
    * handle\_round\_end(): Processes the end of a round, determines winner, records results with the Tournament object, and transitions state.  
    * start\_new\_tournament(): Resets tournament and starts a new game.  
    * start\_next\_round(): Sets up for the subsequent round.  
    * draw\_playing(), draw\_scores(), draw\_start\_screen(), draw\_round\_over(), draw\_tournament\_end(): Specific rendering functions.

### 4.4. From tournament.py (Inferred based on usage)

* **Tournament Class**  
  * **Purpose:** Manages the overarching tournament structure, tracking scores, wins, and determining the final victor over multiple rounds.  
  * **Key Attributes (inferred):** config (GameConfig instance), results (list of round data), snake1\_wins, snake2\_wins, current\_round, snake1\_name, snake2\_name, draw\_rounds, crashed\_rounds, total\_snake1\_apples, total\_snake2\_apples.  
  * **Key Methods (inferred):**  
    * \_\_init\_\_(config): Initializes the tournament.  
    * record\_round(winner, snake1\_score, snake2\_score, ...): Records the outcome and statistics of a completed round.  
    * is\_tournament\_over(): Checks if the conditions for ending the tournament have been met (e.g., max rounds played, one player has enough wins).  
    * get\_winner(): Returns the name of the tournament winner, or None for a draw.  
    * save\_to\_csv(): Saves the detailed tournament results to a CSV file.

## 5\. Key Standalone Functions (from game\_settings.py)

* **get\_distance(pos1: Tuple\[int, int\], pos2: Tuple\[int, int\]) \-\> float**  
  * Calculates the Euclidean distance between two points (x,y) on the grid.  
  * Used by bots for heuristics (e.g., distance to food, opponent).  
* **generate\_spawn\_positions() \-\> Tuple\[Tuple\[int, int\], Tuple\[int, int\], List\[Tuple\[int, int\]\]\]**  
  * Generates random starting positions for the two snakes, ensuring they are a minimum distance apart.  
  * Also generates initial positions for a set number of food items, avoiding snake spawn points.  
  * Returns: (snake1\_spawn, snake2\_spawn, food\_positions\_list).  
* **is\_safe(snake: Snake, new\_head\_pos: List\[int\], other\_snake: Optional\[Snake\] \= None) \-\> bool**  
  * Checks if a proposed new\_head\_pos for a snake is safe to move into.  
  * Considers:  
    * Wall collisions (boundaries of GRID\_WIDTH, GRID\_HEIGHT).  
    * Self-collision (running into its own body, excluding the neck).  
    * Collision with other\_snake's body segments.  
  * Does NOT inherently check for traps; trap collision is handled separately after a move is made.

## 6\. Game Flow

1. **Game Start:**  
   1. The SnakeGame is initialized.  
   2. The START screen is displayed: "Snake Tournament," "Press SPACE to begin."  
2. **Tournament Initialization:**  
   1. Player presses SPACE.  
   2. start\_new\_tournament() is called:  
      1. A new Tournament object is created.  
      2. game\_state transitions to PLAYING.  
      3. current\_round is set to 1\.  
      4. reset\_round() is called.  
3. **Round Start (reset\_round):**  
   1. Snake spawn positions and initial food layout are generated (positions swapped for subsequent rounds if swap\_positions is true).  
   2. Snake objects for snake1 and snake2 are created/reset with their respective bot names as agent\_id.  
   3. Food object is initialized with the generated layout.  
   4. Trap objects are spawned.  
   5. Round timers are initialized.  
4. **Gameplay Loop (SnakeGame.update() when game\_state \== GameState.PLAYING):**  
   1. **Bot Decisions:** bot1.decide\_move() and bot2.decide\_move() are called to get the next intended moves.  
   2. **Snake Updates:** snake.change\_direction() sets the chosen move, then snake.update(dt):  
      1. Actual direction is updated.  
      2. Snake head moves one grid cell.  
      3. Body segments follow.  
      4. Growth is handled if food was recently eaten.  
      5. Self-collision and wall collision checks occur, potentially setting snake.alive \= False.  
   3. **Advantage Time:** If a snake dies by self-collision/wall, an advantage timer starts for the opponent. If the opponent also dies within this window, it might be considered a mutual destruction or affect scoring.  
   4. **Collision Checks (check\_collisions()):**  
      1. Food collision: If head on food, snake grows, score increases, food respawns.  
      2. Trap collision: If head on trap, snake penalized (score, length), gains shield, trap removed.  
      3. Snake-on-snake collision: Penalties, shields applied as per snake.check\_collision\_with\_other().  
   5. **Round End Conditions Checked (check\_round\_end()):** Time up, both snakes dead, or no food left.  
   6. **Drawing (SnakeGame.draw()):** The game board, snakes, food, traps, and HUD (scores, time, round info) are rendered.  
5. **Round End (handle\_round\_end()):**  
   1. The winner of the round (or draw) is determined based on aliveness and scores.  
   2. tournament.record\_round() is called with all relevant statistics.  
   3. If tournament.is\_tournament\_over() is true:  
      1. final\_winner is determined via tournament.get\_winner().  
      2. tournament.save\_to\_csv() is called.  
      3. show\_final\_results() prints to console.  
      4. game\_state becomes GAME\_OVER.  
   4. Else (tournament continues):  
      1. game\_state becomes ROUND\_OVER.  
   5. The ROUND\_OVER screen is displayed, showing round winner and tournament progress. Press SPACE.  
6. **Next Round / Tournament End:**  
   1. If ROUND\_OVER: Pressing SPACE calls start\_next\_round(), which calls reset\_round() (often with swapped positions) and sets game\_state back to PLAYING.  
   2. If GAME\_OVER: The TOURNAMENT\_END screen shows the final winner and score. Pressing SPACE calls quit\_game().

## 7\. How to Run the Game

1. **Prerequisites:**  
   1. Ensure Python 3 is installed.  
   2. Install the Pygame library: pip install pygame  
2. **Execution:**  
   1. Download or clone all project files (game\_settings.py, bot.py, main.py/snake\_game.py, and any other dependencies like tournament.py if it's separate).  
   2. Open a terminal or command prompt.  
   3. Navigate to the directory where you saved the files.  
   4. Run the main game script: python main.py (replace main.py with the actual filename of the script containing the SnakeGame class and the if \_\_name\_\_ \== "\_\_main\_\_": block).

## 8\. Customization and Extension

* **Adding New Bots:**  
  * Open bot.py.  
  * Create a new class that inherits from the base Bot class.

| class MyNewBot(Bot):     def \_\_init\_\_(self):         super().\_\_init\_\_()         self.name \= "MyNewBotName"         *\# Optionally, define bot-specific config/weights*         *\# self.config\['my\_param'\] \= value*     def decide\_move(self, snake: Snake, food: Food, opponent: Optional\[Snake\] \= None) \-\> Tuple\[int, int\]:         *\# Implement your custom decision-making logic here*         *\# Access snake.get\_head\_position(), food.positions, opponent details, etc.*         *\# Use Direction.UP, Direction.DOWN, etc. or (dx,dy) tuples for moves*         *\# Example: return Direction.UP*         chosen\_move \= (0, \-1) *\# Placeholder for UP*         *\# ... your logic ...*         return chosen\_move |
| :---- |

*   
  * Open main.py (or your main game script).  
  * Import your new bot: from bot import MyNewBot (if not already importing all with \*).  
  * In the SnakeGame.\_\_init\_\_ method, instantiate your bot for self.bot1 or self.bot2:

| *\# self.bot1 \= StrategicBot()* self.bot1 \= MyNewBot() *\# Use your new bot* *\# self.bot2 \= GreedyBot()* |
| :---- |

*   
* **Adjusting Game Rules:**  
  * Most game parameters can be modified by changing the default values in the GameConfig dataclass definition within game\_settings.py. For example, to make rounds longer, change round\_time. To have more traps, change trap\_count.  
* **Modifying Bot Behavior:**  
  * The config dictionary within each Bot subclass (e.g., GreedyBot, StrategicBot) can be used to tune their behavior by adjusting weights like food\_weight, danger\_weight, etc., without changing their core logic.

# Snake Game Project Documentation

## 1\. Introduction

This document outlines the design, mechanics, and structure of the Snake Game project. It's a 2-player (or Player vs. AI, AI vs. AI) version of the classic Snake game, built using Python and the Pygame library. The game features multiple AI bot strategies, a tournament mode, various game elements like traps, and configurable game settings.

## 2\. Core Game Mechanics

The game revolves around controlling a snake to eat food, grow longer, and achieve a higher score than the opponent, all while avoiding hazards.

* **Objective:**  
  * Grow your snake by eating food.  
  * Score points for each food item consumed.  
  * Outlive your opponent or have a higher score when the round ends.  
  * Win the majority of rounds in a tournament.  
* **Snakes:**  
  * **Movement:** Snakes move at a constant speed on a grid. Players/bots can change the snake's direction (Up, Down, Left, Right), but cannot immediately reverse into their own body.  
  * **Growth:** Eating food increases the snake's length by a configured number of segments (growth\_per\_food).  
  * **Collision:**  
    * **Self-Collision:** If a snake's head collides with its own body, it dies (or enters an "advantage time" for the opponent).  
    * **Wall Collision:** Colliding with the game boundaries results in death.  
    * **Opponent Collision:**  
      * **Head-to-Head:** Both snakes may receive penalties (lose segments, score reduction) and a temporary shield. The outcome can depend on relative scores.  
      * **Head-to-Body:** The snake whose head hits an opponent's body receives penalties and a shield.  
* **Food:**  
  * Appears at random unoccupied locations on the grid.  
  * When eaten, it disappears, increases the consumer's score and length, and a new food item may spawn elsewhere.  
* **Traps:**  
  * Appear at random unoccupied locations (avoiding food and snakes initially).  
  * If a snake's head hits a trap:  
    * The snake loses score points (trap\_penalty).  
    * The snake loses segments (trap\_segment\_penalty).  
    * The snake gains a temporary shield.  
    * The trap disappears.  
* **Walls:**  
  * The game area is enclosed by walls. Hitting a wall means the snake dies and is out for the current round.  
* **Scoring:**  
  * Primarily by eating food (+1 point per food, or as configured).  
  * Penalties for hitting traps or colliding with opponents reduce the score.  
  * Minimum snake length is enforced.  
* **Rounds & Timers:**  
  * A game (tournament match) consists of multiple rounds (max\_rounds).  
  * Each round has a time limit (round\_time).  
  * A round ends if:  
    * Time runs out.  
    * Both snakes die.  
    * All food is eaten (if this is a defined win condition, though currently it ends the round).  
  * The winner of a round is the snake that is alive at the end, or if both are alive, the one with the higher score. If scores are equal, it's a draw for the round.  
* **Tournament Mode:**  
  * The game is structured as a tournament between two agents (bots or a player).  
  * Wins, losses, and scores are tracked across rounds.  
  * The agent winning the most rounds wins the tournament. Tie-breaking rules (like total score or extra rounds) can apply.  
  * **Advantage Time:** If one snake dies due to self-collision or wall collision, the other snake gets a period of "advantage time" (advantage\_time). If the surviving snake also dies during this period, it may affect the round outcome. If it survives, it solidifies its win for that scenario.  
  * **Early Victory:** A significant point difference (early\_victory\_diff) after a minimum number of rounds (min\_rounds\_for\_early\_victory) can result in an early tournament win.  
* **Shield Mechanic:**  
  * After certain collisions (head-to-head, head-to-body with opponent, or hitting a trap), a snake receives a temporary shield (shield\_duration).  
  * While shielded, the snake is typically immune to further collision penalties with other snakes.  
  * Visually indicated by a flashing effect.

## 3\. Project File Structure

The project is organized into several Python files:

* **game\_settings.py:** Defines all core game entities (Snake, Food, Trap), game constants (screen dimensions, grid size, colors), the GameConfig dataclass for game rules, the GameState enum, and utility functions like get\_distance and is\_safe.  
* **bot.py:** Contains the base Bot class and specific AI implementations (RandomBot, GreedyBot, StrategicBot, CustomBot, UserBot). This is where agent decision-making logic resides.  
* **main.py (or equivalent, e.g., snake\_game.py):** The main script that initializes Pygame, runs the game loop, manages game states, handles user input, renders graphics, and integrates the bots and tournament logic. It contains the SnakeGame class.  
* **tournament.py (inferred):** This file (not provided but used by SnakeGame) is responsible for managing the logic of a tournament: tracking round results, scores, wins, determining the overall winner, and saving tournament statistics.

## 4\. Key Classes and Their Logic

### 4.1. From game\_settings.py

* **Direction Class**  
  * **Purpose:** Provides named constants for movement vectors (tuples like (dx, dy)) and a utility to find the opposite direction. Enhances code readability.  
  * **Key Attributes:** RIGHT \= (1, 0\), LEFT \= (-1, 0\), UP \= (0, \-1), DOWN \= (0, 1\).  
  * **Key Methods:** opposite(direction): Returns the inverse of a given direction tuple.  
* **GameState Enum**  
  * **Purpose:** Defines distinct states the game can be in, controlling the main game loop's behavior.  
  * **Values:** START, PLAYING, GAME\_OVER, DRAW, ROUND\_OVER.  
* **GameConfig Dataclass**  
  * **Purpose:** A centralized container for all configurable game parameters, making it easy to tweak game rules and behavior.  
  * **Key Attributes:** tournament\_mode, max\_rounds, round\_time, trap\_count, trap\_penalty, shield\_duration, initial\_food, growth\_per\_food, min\_snake\_length, early\_victory\_diff, etc.  
* **GameObject Class**  
  * **Purpose:** An abstract base class for any object in the game that needs to be drawn on the screen.  
  * **Key Methods:** draw(surface): Abstract method to be implemented by subclasses for rendering.  
* **Snake Class (inherits GameObject)**  
  * **Purpose:** Represents a snake, managing its segments, movement, state, score, and interactions.  
  * **Key Attributes:**  
    * segments: A deque of \[x,y\] coordinates representing the snake's body, head at index 0\.  
    * direction: Current actual direction of movement (a tuple like (1,0)).  
    * next\_direction: Buffered direction for the next move tick.  
    * score: The snake's current score.  
    * alive: Boolean indicating if the snake is currently alive.  
    * shield\_timer: Countdown for how long the shield remains active.  
    * agent\_id: Name of the bot/player controlling this snake.  
    * config: An instance of GameConfig.  
  * **Key Methods:**  
    * reset(start\_x, start\_y): Initializes/resets the snake to a starting state.  
    * update(dt): Handles movement logic per frame, including moving segments, growing, and checking for self-collision or wall collision. dt is delta time.  
    * change\_direction(new\_dir): Sets next\_direction if new\_dir isn't opposite to current direction.  
    * check\_collision\_with\_other(other\_snake): Manages logic for head-to-head and head-to-body collisions with another snake, applying penalties and shields.  
    * get\_head\_position(): Returns a copy of the head's \[x,y\] coordinates.  
    * draw(surface): Renders the snake (head with eyes, body segments, shield effect).  
* **Food Class (inherits GameObject)**  
  * **Purpose:** Manages food items in the game.  
  * **Key Attributes:** positions: A list of (x,y) tuples for all active food items.  
  * **Key Methods:**  
    * spawn\_multiple(num\_foods, snake\_segments): Spawns a specified number of food items in valid locations.  
    * check\_collision(head\_position): Checks if a snake's head has collided with any food; if so, removes the food.  
    * draw(surface): Renders all food items.  
* **Trap Class (inherits GameObject)**  
  * **Purpose:** Manages traps in the game.  
  * **Key Attributes:** positions: A list of (x,y) tuples for all active traps. config: An instance of GameConfig.  
  * **Key Methods:**  
    * spawn\_multiple(num\_traps, snake\_segments, food\_positions): Spawns traps in valid locations.  
    * get\_positions():It will return all positions of traps in the game board.  
    * check\_collision(snake): Checks if a given snake has collided with a trap; if so, applies penalties and shield to the snake and removes the trap.  
    * draw(surface): Renders all traps.

### 4.2. From bot.py

* **Bot Class (Base)**  
  * **Purpose:** An abstract base class defining the interface for all AI agents.  
  * **Key Attributes:** name (string identifier), config (dictionary for bot-specific weights/parameters).  
  * **Key Methods:** decide\_move(snake, food, opponent): Abstract method. Subclasses must implement this to return a direction tuple (dx, dy) representing the chosen move.  
* **RandomBot Class (inherits Bot)**  
  * **Logic:** Chooses a random valid direction (not opposite to current movement).  
* **GreedyBot Class (inherits Bot)**  
  * **Logic:** Primarily aims for the nearest food. Includes basic safety checks (avoiding walls, self, opponent) and a simple mobility score to avoid getting trapped.  
* **StrategicBot Class (inherits Bot)**  
  * **Logic:** A more advanced bot that considers:  
    * Safer food choices (e.g., food further from the opponent).  
    * Predicting the opponent's next few moves to avoid collisions or contest areas.  
    * Mobility and available space.  
    * Advanced danger detection.

### 4.3. From main.py (or equivalent)

* **SnakeGame Class**  
  * **Purpose:** The main class that initializes Pygame, manages the game window, orchestrates the game loop, handles events, updates game states, and renders all visual elements.  
  * **Key Attributes:**  
    * screen: The Pygame display surface.  
    * clock: Pygame clock for managing frame rate.  
    * game\_state: Current state of the game (instance of GameState).  
    * config: An instance of GameConfig.  
    * snake1, snake2: Instances of the Snake class.  
    * food: Instance of the Food class.  
    * traps: Instance of the Trap class.  
    * bot1, bot2: Instances of Bot subclasses.  
    * tournament: Instance of the Tournament class.  
    * round\_start\_time, snake1\_advantage\_time, etc.: Timers for round and advantage logic.  
  * **Key Methods:**  
    * run(): Contains the main game loop.  
    * handle\_events(): Processes Pygame events (keyboard input, quit).  
    * update(): Updates the game logic each frame based on the current game\_state. This includes getting moves from bots, updating snakes, checking collisions, and managing round timers/conditions.  
    * draw(): Renders the current game scene based on game\_state (e.g., start screen, playing field, round over screen).  
    * reset\_round(swap\_positions): Initializes snakes, food, and traps for a new round.  
    * check\_collisions(): Centralized method to check food, trap, and snake-on-snake collisions.  
    * handle\_round\_end(): Processes the end of a round, determines winner, records results with the Tournament object, and transitions state.  
    * start\_new\_tournament(): Resets tournament and starts a new game.  
    * start\_next\_round(): Sets up for the subsequent round.  
    * draw\_playing(), draw\_scores(), draw\_start\_screen(), draw\_round\_over(), draw\_tournament\_end(): Specific rendering functions.

### 4.4. From tournament.py (Inferred based on usage)

* **Tournament Class**  
  * **Purpose:** Manages the overarching tournament structure, tracking scores, wins, and determining the final victor over multiple rounds.  
  * **Key Attributes (inferred):** config (GameConfig instance), results (list of round data), snake1\_wins, snake2\_wins, current\_round, snake1\_name, snake2\_name, draw\_rounds, crashed\_rounds, total\_snake1\_apples, total\_snake2\_apples.  
  * **Key Methods (inferred):**  
    * \_\_init\_\_(config): Initializes the tournament.  
    * record\_round(winner, snake1\_score, snake2\_score, ...): Records the outcome and statistics of a completed round.  
    * is\_tournament\_over(): Checks if the conditions for ending the tournament have been met (e.g., max rounds played, one player has enough wins).  
    * get\_winner(): Returns the name of the tournament winner, or None for a draw.  
    * save\_to\_csv(): Saves the detailed tournament results to a CSV file.

## 5\. Key Standalone Functions (from game\_settings.py)

* **get\_distance(pos1: Tuple\[int, int\], pos2: Tuple\[int, int\]) \-\> float**  
  * Calculates the Euclidean distance between two points (x,y) on the grid.  
  * Used by bots for heuristics (e.g., distance to food, opponent).  
* **generate\_spawn\_positions() \-\> Tuple\[Tuple\[int, int\], Tuple\[int, int\], List\[Tuple\[int, int\]\]\]**  
  * Generates random starting positions for the two snakes, ensuring they are a minimum distance apart.  
  * Also generates initial positions for a set number of food items, avoiding snake spawn points.  
  * Returns: (snake1\_spawn, snake2\_spawn, food\_positions\_list).  
* **is\_safe(snake: Snake, new\_head\_pos: List\[int\], other\_snake: Optional\[Snake\] \= None) \-\> bool**  
  * Checks if a proposed new\_head\_pos for a snake is safe to move into.  
  * Considers:  
    * Wall collisions (boundaries of GRID\_WIDTH, GRID\_HEIGHT).  
    * Self-collision (running into its own body, excluding the neck).  
    * Collision with other\_snake's body segments.  
  * Does NOT inherently check for traps; trap collision is handled separately after a move is made.

## 6\. Game Flow

1. **Game Start:**  
   1. The SnakeGame is initialized.  
   2. The START screen is displayed: "Snake Tournament," "Press SPACE to begin."  
2. **Tournament Initialization:**  
   1. Player presses SPACE.  
   2. start\_new\_tournament() is called:  
      1. A new Tournament object is created.  
      2. game\_state transitions to PLAYING.  
      3. current\_round is set to 1\.  
      4. reset\_round() is called.  
3. **Round Start (reset\_round):**  
   1. Snake spawn positions and initial food layout are generated (positions swapped for subsequent rounds if swap\_positions is true).  
   2. Snake objects for snake1 and snake2 are created/reset with their respective bot names as agent\_id.  
   3. Food object is initialized with the generated layout.  
   4. Trap objects are spawned.  
   5. Round timers are initialized.  
4. **Gameplay Loop (SnakeGame.update() when game\_state \== GameState.PLAYING):**  
   1. **Bot Decisions:** bot1.decide\_move() and bot2.decide\_move() are called to get the next intended moves.  
   2. **Snake Updates:** snake.change\_direction() sets the chosen move, then snake.update(dt):  
      1. Actual direction is updated.  
      2. Snake head moves one grid cell.  
      3. Body segments follow.  
      4. Growth is handled if food was recently eaten.  
      5. Self-collision and wall collision checks occur, potentially setting snake.alive \= False.  
   3. **Advantage Time:** If a snake dies by self-collision/wall, an advantage timer starts for the opponent. If the opponent also dies within this window, it might be considered a mutual destruction or affect scoring.  
   4. **Collision Checks (check\_collisions()):**  
      1. Food collision: If head on food, snake grows, score increases, food respawns.  
      2. Trap collision: If head on trap, snake penalized (score, length), gains shield, trap removed.  
      3. Snake-on-snake collision: Penalties, shields applied as per snake.check\_collision\_with\_other().  
   5. **Round End Conditions Checked (check\_round\_end()):** Time up, both snakes dead, or no food left.  
   6. **Drawing (SnakeGame.draw()):** The game board, snakes, food, traps, and HUD (scores, time, round info) are rendered.  
5. **Round End (handle\_round\_end()):**  
   1. The winner of the round (or draw) is determined based on aliveness and scores.  
   2. tournament.record\_round() is called with all relevant statistics.  
   3. If tournament.is\_tournament\_over() is true:  
      1. final\_winner is determined via tournament.get\_winner().  
      2. tournament.save\_to\_csv() is called.  
      3. show\_final\_results() prints to console.  
      4. game\_state becomes GAME\_OVER.  
   4. Else (tournament continues):  
      1. game\_state becomes ROUND\_OVER.  
   5. The ROUND\_OVER screen is displayed, showing round winner and tournament progress. Press SPACE.  
6. **Next Round / Tournament End:**  
   1. If ROUND\_OVER: Pressing SPACE calls start\_next\_round(), which calls reset\_round() (often with swapped positions) and sets game\_state back to PLAYING.  
   2. If GAME\_OVER: The TOURNAMENT\_END screen shows the final winner and score. Pressing SPACE calls quit\_game().

## 7\. How to Run the Game

1. **Prerequisites:**  
   1. Ensure Python 3 is installed.  
   2. Install the Pygame library: pip install pygame  
2. **Execution:**  
   1. Download or clone all project files (game\_settings.py, bot.py, main.py/snake\_game.py, and any other dependencies like tournament.py if it's separate).  
   2. Open a terminal or command prompt.  
   3. Navigate to the directory where you saved the files.  
   4. Run the main game script: python main.py (replace main.py with the actual filename of the script containing the SnakeGame class and the if \_\_name\_\_ \== "\_\_main\_\_": block).

## 8\. Customization and Extension

* **Adding New Bots:**  
  * Open bot.py.  
  * Create a new class that inherits from the base Bot class.

| class MyNewBot(Bot):     def \_\_init\_\_(self):         super().\_\_init\_\_()         self.name \= "MyNewBotName"         *\# Optionally, define bot-specific config/weights*         *\# self.config\['my\_param'\] \= value*     def decide\_move(self, snake: Snake, food: Food, opponent: Optional\[Snake\] \= None) \-\> Tuple\[int, int\]:         *\# Implement your custom decision-making logic here*         *\# Access snake.get\_head\_position(), food.positions, opponent details, etc.*         *\# Use Direction.UP, Direction.DOWN, etc. or (dx,dy) tuples for moves*         *\# Example: return Direction.UP*         chosen\_move \= (0, \-1) *\# Placeholder for UP*         *\# ... your logic ...*         return chosen\_move |
| :---- |

*   
  * Open main.py (or your main game script).  
  * Import your new bot: from bot import MyNewBot (if not already importing all with \*).  
  * In the SnakeGame.\_\_init\_\_ method, instantiate your bot for self.bot1 or self.bot2:

| *\# self.bot1 \= StrategicBot()* self.bot1 \= MyNewBot() *\# Use your new bot* *\# self.bot2 \= GreedyBot()* |
| :---- |

*   
* **Adjusting Game Rules:**  
  * Most game parameters can be modified by changing the default values in the GameConfig dataclass definition within game\_settings.py. For example, to make rounds longer, change round\_time. To have more traps, change trap\_count.  
* **Modifying Bot Behavior:**  
  * The config dictionary within each Bot subclass (e.g., GreedyBot, StrategicBot) can be used to tune their behavior by adjusting weights like food\_weight, danger\_weight, etc., without changing their core logic.

