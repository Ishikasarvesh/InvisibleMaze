import random
import sys

import pygame


# ---------------------------------------------------------
# PYGAME INITIALIZATION
# ---------------------------------------------------------

pygame.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Invisible Maze")

clock = pygame.time.Clock()


# ---------------------------------------------------------
# COLORS
# ---------------------------------------------------------

BACKGROUND_COLOR = (8, 10, 18)
HIDDEN_COLOR = (4, 5, 10)
VISIBLE_PATH_COLOR = (35, 40, 52)
WALL_COLOR = (80, 88, 110)
PLAYER_COLOR = (255, 220, 100)
EXIT_COLOR = (70, 230, 150)
TEXT_COLOR = (235, 235, 245)
FOOTPRINT_COLOR = (65, 70, 90)


# ---------------------------------------------------------
# GAME SETTINGS
# ---------------------------------------------------------

ROWS = 21
COLS = 21
CELL_SIZE = 28

MAZE_WIDTH = COLS * CELL_SIZE
MAZE_HEIGHT = ROWS * CELL_SIZE

MAZE_START_X = (SCREEN_WIDTH - MAZE_WIDTH) // 2
MAZE_START_Y = 75

VISIBILITY_RADIUS = 2

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
large_font = pygame.font.SysFont("arial", 52, bold=True)


# ---------------------------------------------------------
# MAZE GENERATION
# ---------------------------------------------------------

def create_empty_maze(rows, cols):
    """
    Creates a maze filled completely with walls.

    1 means wall.
    0 means open path.
    """

    return [[1 for _ in range(cols)] for _ in range(rows)]


def get_unvisited_neighbors(row, col, maze):
    """
    Returns cells that are two positions away and have
    not yet been visited.
    """

    possible_directions = [
        (-2, 0),
        (2, 0),
        (0, -2),
        (0, 2)
    ]

    neighbors = []

    for row_change, col_change in possible_directions:
        new_row = row + row_change
        new_col = col + col_change

        inside_rows = 1 <= new_row < ROWS - 1
        inside_cols = 1 <= new_col < COLS - 1

        if inside_rows and inside_cols:
            if maze[new_row][new_col] == 1:
                neighbors.append((new_row, new_col))

    return neighbors


def generate_maze():
    """
    Generates a random maze using recursive backtracking.
    """

    maze = create_empty_maze(ROWS, COLS)

    start_row = 1
    start_col = 1

    maze[start_row][start_col] = 0

    stack = [(start_row, start_col)]

    while stack:
        current_row, current_col = stack[-1]

        neighbors = get_unvisited_neighbors(
            current_row,
            current_col,
            maze
        )

        if neighbors:
            next_row, next_col = random.choice(neighbors)

            wall_row = (current_row + next_row) // 2
            wall_col = (current_col + next_col) // 2

            maze[wall_row][wall_col] = 0
            maze[next_row][next_col] = 0

            stack.append((next_row, next_col))

        else:
            stack.pop()

    return maze


# ---------------------------------------------------------
# GAME VARIABLES
# ---------------------------------------------------------

maze = generate_maze()

player_row = 1
player_col = 1

exit_row = ROWS - 2
exit_col = COLS - 2

maze[exit_row][exit_col] = 0

moves = 0
game_won = False

visited_cells = {(player_row, player_col)}

start_time = pygame.time.get_ticks()


# ---------------------------------------------------------
# GAME FUNCTIONS
# ---------------------------------------------------------

def reset_game():
    """
    Creates a new maze and resets all game values.
    """

    global maze
    global player_row
    global player_col
    global moves
    global game_won
    global visited_cells
    global start_time

    maze = generate_maze()

    player_row = 1
    player_col = 1

    maze[exit_row][exit_col] = 0

    moves = 0
    game_won = False

    visited_cells = {(player_row, player_col)}

    start_time = pygame.time.get_ticks()


def can_move(new_row, new_col):
    """
    Checks whether the player can enter a particular cell.
    """

    inside_maze = (
        0 <= new_row < ROWS
        and 0 <= new_col < COLS
    )

    if not inside_maze:
        return False

    return maze[new_row][new_col] == 0


def move_player(row_change, col_change):
    """
    Attempts to move the player in a given direction.
    """

    global player_row
    global player_col
    global moves
    global game_won

    if game_won:
        return

    new_row = player_row + row_change
    new_col = player_col + col_change

    if can_move(new_row, new_col):
        player_row = new_row
        player_col = new_col

        moves += 1

        visited_cells.add((player_row, player_col))

        if player_row == exit_row and player_col == exit_col:
            game_won = True


def is_cell_visible(row, col):
    """
    Returns True when a maze cell is close enough
    to the player to be visible.
    """

    row_distance = abs(row - player_row)
    col_distance = abs(col - player_col)

    distance = row_distance + col_distance

    return distance <= VISIBILITY_RADIUS


def get_elapsed_time():
    """
    Returns the number of seconds played.
    """

    current_time = pygame.time.get_ticks()
    elapsed_milliseconds = current_time - start_time

    return elapsed_milliseconds // 1000


# ---------------------------------------------------------
# DRAWING FUNCTIONS
# ---------------------------------------------------------

def draw_glow(center_x, center_y):
    """
    Draws transparent circles around the player to
    create a basic torchlight effect.
    """

    glow_surface = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.SRCALPHA
    )

    pygame.draw.circle(
        glow_surface,
        (255, 220, 120, 18),
        (center_x, center_y),
        CELL_SIZE * 4
    )

    pygame.draw.circle(
        glow_surface,
        (255, 220, 120, 30),
        (center_x, center_y),
        CELL_SIZE * 3
    )

    pygame.draw.circle(
        glow_surface,
        (255, 220, 120, 45),
        (center_x, center_y),
        CELL_SIZE * 2
    )

    screen.blit(glow_surface, (0, 0))


def draw_maze():
    """
    Draws visible cells around the player.
    Everything outside the visibility radius remains dark.
    """

    for row in range(ROWS):
        for col in range(COLS):

            x = MAZE_START_X + col * CELL_SIZE
            y = MAZE_START_Y + row * CELL_SIZE

            cell_rectangle = pygame.Rect(
                x,
                y,
                CELL_SIZE,
                CELL_SIZE
            )

            visible = is_cell_visible(row, col)
            visited = (row, col) in visited_cells

            if visible:
                if maze[row][col] == 1:
                    pygame.draw.rect(
                        screen,
                        WALL_COLOR,
                        cell_rectangle
                    )
                else:
                    pygame.draw.rect(
                        screen,
                        VISIBLE_PATH_COLOR,
                        cell_rectangle
                    )

                    pygame.draw.rect(
                        screen,
                        (50, 55, 70),
                        cell_rectangle,
                        1
                    )

            elif visited:
                pygame.draw.rect(
                    screen,
                    FOOTPRINT_COLOR,
                    cell_rectangle
                )

            else:
                pygame.draw.rect(
                    screen,
                    HIDDEN_COLOR,
                    cell_rectangle
                )


def draw_exit():
    """
    Draws the exit only when it is within the player's light.
    """

    if not is_cell_visible(exit_row, exit_col):
        return

    x = MAZE_START_X + exit_col * CELL_SIZE
    y = MAZE_START_Y + exit_row * CELL_SIZE

    exit_rectangle = pygame.Rect(
        x + 5,
        y + 5,
        CELL_SIZE - 10,
        CELL_SIZE - 10
    )

    pygame.draw.rect(
        screen,
        EXIT_COLOR,
        exit_rectangle,
        border_radius=5
    )


def draw_player():
    """
    Draws the player as a glowing circle.
    """

    center_x = (
        MAZE_START_X
        + player_col * CELL_SIZE
        + CELL_SIZE // 2
    )

    center_y = (
        MAZE_START_Y
        + player_row * CELL_SIZE
        + CELL_SIZE // 2
    )

    draw_glow(center_x, center_y)

    pygame.draw.circle(
        screen,
        PLAYER_COLOR,
        (center_x, center_y),
        CELL_SIZE // 3
    )

    pygame.draw.circle(
        screen,
        (255, 245, 190),
        (center_x - 3, center_y - 3),
        4
    )


def draw_information():
    """
    Shows moves, time and controls.
    """

    elapsed_time = get_elapsed_time()

    move_text = font.render(
        f"Moves: {moves}",
        True,
        TEXT_COLOR
    )

    time_text = font.render(
        f"Time: {elapsed_time}s",
        True,
        TEXT_COLOR
    )

    control_text = small_font.render(
        "Move: Arrow Keys / WASD     Restart: R",
        True,
        TEXT_COLOR
    )

    screen.blit(move_text, (30, 20))
    screen.blit(time_text, (SCREEN_WIDTH - 150, 20))

    screen.blit(
        control_text,
        (
            SCREEN_WIDTH // 2 - control_text.get_width() // 2,
            SCREEN_HEIGHT - 35
        )
    )


def draw_win_screen():
    """
    Displays a semi-transparent result screen.
    """

    if not game_won:
        return

    overlay = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    title = large_font.render(
        "YOU ESCAPED!",
        True,
        EXIT_COLOR
    )

    result = font.render(
        f"Moves: {moves}    Time: {get_elapsed_time()} seconds",
        True,
        TEXT_COLOR
    )

    restart_message = small_font.render(
        "Press R to generate a new maze",
        True,
        TEXT_COLOR
    )

    screen.blit(
        title,
        (
            SCREEN_WIDTH // 2 - title.get_width() // 2,
            245
        )
    )

    screen.blit(
        result,
        (
            SCREEN_WIDTH // 2 - result.get_width() // 2,
            325
        )
    )

    screen.blit(
        restart_message,
        (
            SCREEN_WIDTH // 2
            - restart_message.get_width() // 2,
            375
        )
    )


# ---------------------------------------------------------
# MAIN GAME LOOP
# ---------------------------------------------------------

running = True

while running:

    # Handle events
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_UP, pygame.K_w):
                move_player(-1, 0)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                move_player(1, 0)

            elif event.key in (pygame.K_LEFT, pygame.K_a):
                move_player(0, -1)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                move_player(0, 1)

            elif event.key == pygame.K_r:
                reset_game()

            elif event.key == pygame.K_ESCAPE:
                running = False

    # Draw everything
    screen.fill(BACKGROUND_COLOR)

    draw_maze()
    draw_exit()
    draw_player()
    draw_information()
    draw_win_screen()

    pygame.display.update()

    clock.tick(60)


pygame.quit()
sys.exit()