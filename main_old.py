import math
import random
import sys

import pygame


# =========================================================
# PYGAME INITIALIZATION
# =========================================================

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 760

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Invisible Maze")

clock = pygame.time.Clock()


# =========================================================
# COLORS
# =========================================================

BACKGROUND = (7, 9, 16)
PANEL_COLOR = (18, 22, 34)

WHITE = (240, 240, 245)
LIGHT_GRAY = (170, 175, 190)
DARK_GRAY = (55, 60, 75)

WALL_COLOR = (80, 88, 110)
PATH_COLOR = (32, 38, 52)
HIDDEN_COLOR = (3, 4, 8)
VISITED_COLOR = (47, 52, 67)

PLAYER_COLOR = (255, 218, 100)
PLAYER_LIGHT = (255, 245, 190)

EXIT_COLOR = (75, 235, 160)
EXIT_LIGHT = (155, 255, 210)

BATTERY_COLOR = (255, 210, 70)
BATTERY_DARK = (155, 110, 20)

GREEN = (75, 220, 145)
YELLOW = (250, 205, 70)
RED = (235, 80, 80)
BLUE = (85, 150, 255)


# =========================================================
# FONTS
# =========================================================

title_font = pygame.font.SysFont("arial", 58, bold=True)
large_font = pygame.font.SysFont("arial", 42, bold=True)
medium_font = pygame.font.SysFont("arial", 26, bold=True)
normal_font = pygame.font.SysFont("arial", 21)
small_font = pygame.font.SysFont("arial", 17)


# =========================================================
# DIFFICULTY SETTINGS
# =========================================================

DIFFICULTIES = {
    "Easy": {
        "rows": 17,
        "cols": 17,
        "starting_battery": 100,
        "battery_drain": 1.2,
        "maximum_visibility": 4,
        "minimum_visibility": 2,
        "battery_pickups": 6,
        "time_multiplier": 1.0,
    },
    "Medium": {
        "rows": 21,
        "cols": 21,
        "starting_battery": 90,
        "battery_drain": 1.8,
        "maximum_visibility": 3,
        "minimum_visibility": 1,
        "battery_pickups": 5,
        "time_multiplier": 1.4,
    },
    "Hard": {
        "rows": 25,
        "cols": 25,
        "starting_battery": 80,
        "battery_drain": 2.5,
        "maximum_visibility": 3,
        "minimum_visibility": 1,
        "battery_pickups": 4,
        "time_multiplier": 1.8,
    },
}


# =========================================================
# BUTTON CLASS
# =========================================================

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False

    def update(self, mouse_position):
        self.hovered = self.rect.collidepoint(mouse_position)

    def draw(self):
        if self.hovered:
            button_color = (70, 85, 120)
            border_color = BLUE
        else:
            button_color = (38, 45, 64)
            border_color = (90, 100, 130)

        pygame.draw.rect(
            screen,
            button_color,
            self.rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            border_color,
            self.rect,
            width=2,
            border_radius=12
        )

        text_surface = medium_font.render(
            self.text,
            True,
            WHITE
        )

        text_rect = text_surface.get_rect(
            center=self.rect.center
        )

        screen.blit(text_surface, text_rect)

    def was_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


# =========================================================
# MAZE GENERATION FUNCTIONS
# =========================================================

def create_empty_maze(rows, cols):
    return [
        [1 for _ in range(cols)]
        for _ in range(rows)
    ]


def get_unvisited_neighbors(row, col, maze, rows, cols):
    directions = [
        (-2, 0),
        (2, 0),
        (0, -2),
        (0, 2),
    ]

    neighbors = []

    for row_change, col_change in directions:
        new_row = row + row_change
        new_col = col + col_change

        inside_maze = (
            1 <= new_row < rows - 1
            and 1 <= new_col < cols - 1
        )

        if inside_maze and maze[new_row][new_col] == 1:
            neighbors.append((new_row, new_col))

    return neighbors


def generate_maze(rows, cols):
    maze = create_empty_maze(rows, cols)

    start_row = 1
    start_col = 1

    maze[start_row][start_col] = 0

    stack = [(start_row, start_col)]

    while stack:
        current_row, current_col = stack[-1]

        neighbors = get_unvisited_neighbors(
            current_row,
            current_col,
            maze,
            rows,
            cols
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


# =========================================================
# MAIN GAME CLASS
# =========================================================

class InvisibleMazeGame:
    def __init__(self):
        self.state = "menu"

        self.difficulty_name = "Easy"
        self.settings = DIFFICULTIES["Easy"]

        self.maze = []
        self.rows = 0
        self.cols = 0

        self.cell_size = 0
        self.maze_start_x = 0
        self.maze_start_y = 100

        self.player_row = 1
        self.player_col = 1

        self.exit_row = 1
        self.exit_col = 1

        self.battery = 100
        self.moves = 0
        self.score = 0

        self.visited_cells = set()
        self.battery_pickups = set()

        self.start_time = 0
        self.pause_started = 0
        self.total_pause_time = 0
        self.win_time = 0

        self.animation_time = 0

        self.easy_button = Button(
            SCREEN_WIDTH // 2 - 140,
            300,
            280,
            60,
            "Easy"
        )

        self.medium_button = Button(
            SCREEN_WIDTH // 2 - 140,
            380,
            280,
            60,
            "Medium"
        )

        self.hard_button = Button(
            SCREEN_WIDTH // 2 - 140,
            460,
            280,
            60,
            "Hard"
        )

        self.resume_button = Button(
            SCREEN_WIDTH // 2 - 130,
            330,
            260,
            60,
            "Resume"
        )

        self.menu_button = Button(
            SCREEN_WIDTH // 2 - 130,
            410,
            260,
            60,
            "Main Menu"
        )

        self.play_again_button = Button(
            SCREEN_WIDTH // 2 - 140,
            440,
            280,
            60,
            "Play Again"
        )

        self.win_menu_button = Button(
            SCREEN_WIDTH // 2 - 140,
            520,
            280,
            60,
            "Main Menu"
        )

    # =====================================================
    # GAME SETUP
    # =====================================================

    def start_new_game(self, difficulty_name):
        self.difficulty_name = difficulty_name
        self.settings = DIFFICULTIES[difficulty_name]

        self.rows = self.settings["rows"]
        self.cols = self.settings["cols"]

        available_width = SCREEN_WIDTH - 100
        available_height = SCREEN_HEIGHT - 190

        self.cell_size = min(
            available_width // self.cols,
            available_height // self.rows
        )

        maze_width = self.cols * self.cell_size

        self.maze_start_x = (
            SCREEN_WIDTH - maze_width
        ) // 2

        self.maze = generate_maze(
            self.rows,
            self.cols
        )

        self.player_row = 1
        self.player_col = 1

        self.exit_row = self.rows - 2
        self.exit_col = self.cols - 2

        self.maze[self.exit_row][self.exit_col] = 0

        self.battery = self.settings["starting_battery"]
        self.moves = 0
        self.score = 0

        self.visited_cells = {
            (self.player_row, self.player_col)
        }

        self.generate_battery_pickups()

        self.start_time = pygame.time.get_ticks()
        self.total_pause_time = 0
        self.pause_started = 0
        self.win_time = 0

        self.state = "playing"

    def generate_battery_pickups(self):
        self.battery_pickups.clear()

        possible_cells = []

        for row in range(1, self.rows - 1):
            for col in range(1, self.cols - 1):
                is_path = self.maze[row][col] == 0

                is_start = row == 1 and col == 1

                is_exit = (
                    row == self.exit_row
                    and col == self.exit_col
                )

                if is_path and not is_start and not is_exit:
                    possible_cells.append((row, col))

        pickup_count = min(
            self.settings["battery_pickups"],
            len(possible_cells)
        )

        selected_cells = random.sample(
            possible_cells,
            pickup_count
        )

        self.battery_pickups = set(selected_cells)

    # =====================================================
    # TIME AND SCORE
    # =====================================================

    def get_elapsed_seconds(self):
        if self.state == "won":
            current_time = self.win_time
        elif self.state == "paused":
            current_time = self.pause_started
        else:
            current_time = pygame.time.get_ticks()

        elapsed = (
            current_time
            - self.start_time
            - self.total_pause_time
        )

        return max(0, elapsed // 1000)

    def calculate_score(self):
        difficulty_bonus = {
            "Easy": 1000,
            "Medium": 1800,
            "Hard": 2800,
        }

        base_score = difficulty_bonus[self.difficulty_name]

        battery_bonus = int(self.battery * 12)
        move_penalty = self.moves * 4
        time_penalty = int(
            self.get_elapsed_seconds()
            * self.settings["time_multiplier"]
            * 2
        )

        self.score = max(
            0,
            base_score
            + battery_bonus
            - move_penalty
            - time_penalty
        )

    # =====================================================
    # VISIBILITY AND BATTERY
    # =====================================================

    def get_visibility_radius(self):
        maximum = self.settings["maximum_visibility"]
        minimum = self.settings["minimum_visibility"]

        if self.battery >= 70:
            return maximum

        if self.battery >= 35:
            return max(minimum, maximum - 1)

        return minimum

    def update_battery(self, delta_time):
        if self.state != "playing":
            return

        drain_amount = (
            self.settings["battery_drain"]
            * delta_time
        )

        self.battery -= drain_amount
        self.battery = max(0, self.battery)

    def collect_battery(self):
        current_position = (
            self.player_row,
            self.player_col
        )

        if current_position in self.battery_pickups:
            self.battery_pickups.remove(current_position)

            self.battery += 30
            self.battery = min(100, self.battery)

    # =====================================================
    # MOVEMENT
    # =====================================================

    def can_move(self, new_row, new_col):
        inside_maze = (
            0 <= new_row < self.rows
            and 0 <= new_col < self.cols
        )

        if not inside_maze:
            return False

        return self.maze[new_row][new_col] == 0

    def move_player(self, row_change, col_change):
        if self.state != "playing":
            return

        new_row = self.player_row + row_change
        new_col = self.player_col + col_change

        if self.can_move(new_row, new_col):
            self.player_row = new_row
            self.player_col = new_col

            self.moves += 1

            self.visited_cells.add(
                (self.player_row, self.player_col)
            )

            self.collect_battery()

            if (
                self.player_row == self.exit_row
                and self.player_col == self.exit_col
            ):
                self.win_time = pygame.time.get_ticks()
                self.state = "won"
                self.calculate_score()

    # =====================================================
    # PAUSE
    # =====================================================

    def pause_game(self):
        if self.state == "playing":
            self.pause_started = pygame.time.get_ticks()
            self.state = "paused"

    def resume_game(self):
        if self.state == "paused":
            pause_duration = (
                pygame.time.get_ticks()
                - self.pause_started
            )

            self.total_pause_time += pause_duration
            self.state = "playing"

    # =====================================================
    # VISIBILITY CHECK
    # =====================================================

    def is_cell_visible(self, row, col):
        radius = self.get_visibility_radius()

        row_distance = abs(row - self.player_row)
        col_distance = abs(col - self.player_col)

        distance = row_distance + col_distance

        return distance <= radius

    # =====================================================
    # DRAWING: MENU
    # =====================================================

    def draw_menu(self):
        screen.fill(BACKGROUND)

        glow_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        pulse = (
            math.sin(self.animation_time * 2)
            + 1
        ) / 2

        glow_radius = int(120 + pulse * 25)

        pygame.draw.circle(
            glow_surface,
            (255, 210, 90, 25),
            (SCREEN_WIDTH // 2, 160),
            glow_radius
        )

        screen.blit(glow_surface, (0, 0))

        title = title_font.render(
            "INVISIBLE MAZE",
            True,
            WHITE
        )

        subtitle = normal_font.render(
            "Escape the darkness before your light disappears.",
            True,
            LIGHT_GRAY
        )

        instruction = small_font.render(
            "Choose a difficulty to begin",
            True,
            LIGHT_GRAY
        )

        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, 135)
            )
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(SCREEN_WIDTH // 2, 205)
            )
        )

        screen.blit(
            instruction,
            instruction.get_rect(
                center=(SCREEN_WIDTH // 2, 255)
            )
        )

        mouse_position = pygame.mouse.get_pos()

        for button in [
            self.easy_button,
            self.medium_button,
            self.hard_button
        ]:
            button.update(mouse_position)
            button.draw()

        control_text = small_font.render(
            "Controls: Arrow Keys or WASD | P to pause | R to restart",
            True,
            DARK_GRAY
        )

        screen.blit(
            control_text,
            control_text.get_rect(
                center=(SCREEN_WIDTH // 2, 620)
            )
        )

    # =====================================================
    # DRAWING: MAZE
    # =====================================================

    def draw_maze(self):
        for row in range(self.rows):
            for col in range(self.cols):
                x = (
                    self.maze_start_x
                    + col * self.cell_size
                )

                y = (
                    self.maze_start_y
                    + row * self.cell_size
                )

                cell_rect = pygame.Rect(
                    x,
                    y,
                    self.cell_size,
                    self.cell_size
                )

                visible = self.is_cell_visible(row, col)
                visited = (row, col) in self.visited_cells

                if visible:
                    if self.maze[row][col] == 1:
                        pygame.draw.rect(
                            screen,
                            WALL_COLOR,
                            cell_rect
                        )
                    else:
                        pygame.draw.rect(
                            screen,
                            PATH_COLOR,
                            cell_rect
                        )

                        pygame.draw.rect(
                            screen,
                            (48, 54, 70),
                            cell_rect,
                            width=1
                        )

                elif visited:
                    pygame.draw.rect(
                        screen,
                        VISITED_COLOR,
                        cell_rect
                    )

                else:
                    pygame.draw.rect(
                        screen,
                        HIDDEN_COLOR,
                        cell_rect
                    )

    # =====================================================
    # DRAWING: BATTERIES
    # =====================================================

    def draw_battery_pickups(self):
        for row, col in self.battery_pickups:
            if not self.is_cell_visible(row, col):
                continue

            center_x = (
                self.maze_start_x
                + col * self.cell_size
                + self.cell_size // 2
            )

            center_y = (
                self.maze_start_y
                + row * self.cell_size
                + self.cell_size // 2
            )

            width = max(8, self.cell_size // 2)
            height = max(12, int(self.cell_size * 0.65))

            body_rect = pygame.Rect(
                center_x - width // 2,
                center_y - height // 2,
                width,
                height
            )

            pygame.draw.rect(
                screen,
                BATTERY_COLOR,
                body_rect,
                border_radius=3
            )

            pygame.draw.rect(
                screen,
                BATTERY_DARK,
                body_rect,
                width=2,
                border_radius=3
            )

            top_rect = pygame.Rect(
                center_x - width // 4,
                body_rect.top - 3,
                width // 2,
                4
            )

            pygame.draw.rect(
                screen,
                BATTERY_COLOR,
                top_rect
            )

    # =====================================================
    # DRAWING: EXIT ANIMATION
    # =====================================================

    def draw_exit(self):
        if not self.is_cell_visible(
            self.exit_row,
            self.exit_col
        ):
            return

        center_x = (
            self.maze_start_x
            + self.exit_col * self.cell_size
            + self.cell_size // 2
        )

        center_y = (
            self.maze_start_y
            + self.exit_row * self.cell_size
            + self.cell_size // 2
        )

        pulse = (
            math.sin(self.animation_time * 4)
            + 1
        ) / 2

        outer_radius = int(
            self.cell_size * 0.35
            + pulse * self.cell_size * 0.12
        )

        glow_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow_surface,
            (80, 255, 175, 45),
            (center_x, center_y),
            outer_radius + 15
        )

        screen.blit(glow_surface, (0, 0))

        pygame.draw.circle(
            screen,
            EXIT_COLOR,
            (center_x, center_y),
            outer_radius
        )

        pygame.draw.circle(
            screen,
            EXIT_LIGHT,
            (center_x, center_y),
            max(3, outer_radius // 2)
        )

    # =====================================================
    # DRAWING: PLAYER ANIMATION
    # =====================================================

    def draw_player(self):
        center_x = (
            self.maze_start_x
            + self.player_col * self.cell_size
            + self.cell_size // 2
        )

        center_y = (
            self.maze_start_y
            + self.player_row * self.cell_size
            + self.cell_size // 2
        )

        pulse = (
            math.sin(self.animation_time * 5)
            + 1
        ) / 2

        visibility = self.get_visibility_radius()

        glow_radius = int(
            self.cell_size
            * (visibility + 0.6)
        )

        glow_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow_surface,
            (255, 215, 100, 18),
            (center_x, center_y),
            glow_radius
        )

        pygame.draw.circle(
            glow_surface,
            (255, 220, 120, 35),
            (center_x, center_y),
            max(10, glow_radius // 2)
        )

        screen.blit(glow_surface, (0, 0))

        player_radius = int(
            self.cell_size * 0.28
            + pulse * 2
        )

        pygame.draw.circle(
            screen,
            PLAYER_COLOR,
            (center_x, center_y),
            player_radius
        )

        pygame.draw.circle(
            screen,
            PLAYER_LIGHT,
            (
                center_x - player_radius // 3,
                center_y - player_radius // 3
            ),
            max(2, player_radius // 4)
        )

    # =====================================================
    # DRAWING: HUD
    # =====================================================

    def get_battery_color(self):
        if self.battery > 55:
            return GREEN

        if self.battery > 25:
            return YELLOW

        return RED

    def draw_hud(self):
        panel_rect = pygame.Rect(
            20,
            15,
            SCREEN_WIDTH - 40,
            65
        )

        pygame.draw.rect(
            screen,
            PANEL_COLOR,
            panel_rect,
            border_radius=12
        )

        difficulty_text = normal_font.render(
            f"Mode: {self.difficulty_name}",
            True,
            WHITE
        )

        move_text = normal_font.render(
            f"Moves: {self.moves}",
            True,
            WHITE
        )

        time_text = normal_font.render(
            f"Time: {self.get_elapsed_seconds()}s",
            True,
            WHITE
        )

        screen.blit(difficulty_text, (40, 35))
        screen.blit(move_text, (235, 35))
        screen.blit(time_text, (390, 35))

        battery_label = normal_font.render(
            f"Torch: {int(self.battery)}%",
            True,
            self.get_battery_color()
        )

        screen.blit(battery_label, (555, 35))

        battery_bar_background = pygame.Rect(
            700,
            34,
            230,
            22
        )

        pygame.draw.rect(
            screen,
            (45, 48, 58),
            battery_bar_background,
            border_radius=8
        )

        battery_width = int(
            230 * self.battery / 100
        )

        battery_bar = pygame.Rect(
            700,
            34,
            battery_width,
            22
        )

        pygame.draw.rect(
            screen,
            self.get_battery_color(),
            battery_bar,
            border_radius=8
        )

        control_text = small_font.render(
            "Move: WASD / Arrow Keys    Pause: P    Restart: R    Menu: M",
            True,
            LIGHT_GRAY
        )

        screen.blit(
            control_text,
            control_text.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    SCREEN_HEIGHT - 22
                )
            )
        )

    # =====================================================
    # DRAWING: BATTERY EMPTY WARNING
    # =====================================================

    def draw_low_battery_warning(self):
        if self.battery > 20:
            return

        warning = medium_font.render(
            "WARNING: TORCH ENERGY CRITICAL",
            True,
            RED
        )

        screen.blit(
            warning,
            warning.get_rect(
                center=(SCREEN_WIDTH // 2, 92)
            )
        )

    # =====================================================
    # DRAWING: PAUSE SCREEN
    # =====================================================

    def draw_pause_screen(self):
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        pause_title = large_font.render(
            "GAME PAUSED",
            True,
            WHITE
        )

        screen.blit(
            pause_title,
            pause_title.get_rect(
                center=(SCREEN_WIDTH // 2, 240)
            )
        )

        mouse_position = pygame.mouse.get_pos()

        self.resume_button.update(mouse_position)
        self.menu_button.update(mouse_position)

        self.resume_button.draw()
        self.menu_button.draw()

        message = small_font.render(
            "Press P or Escape to continue",
            True,
            LIGHT_GRAY
        )

        screen.blit(
            message,
            message.get_rect(
                center=(SCREEN_WIDTH // 2, 510)
            )
        )

    # =====================================================
    # DRAWING: WIN SCREEN
    # =====================================================

    def draw_win_screen(self):
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        pulse = (
            math.sin(self.animation_time * 3)
            + 1
        ) / 2

        title_y = 145 + int(pulse * 5)

        win_title = title_font.render(
            "YOU ESCAPED!",
            True,
            EXIT_COLOR
        )

        screen.blit(
            win_title,
            win_title.get_rect(
                center=(SCREEN_WIDTH // 2, title_y)
            )
        )

        result_lines = [
            f"Difficulty: {self.difficulty_name}",
            f"Moves: {self.moves}",
            f"Time: {self.get_elapsed_seconds()} seconds",
            f"Torch remaining: {int(self.battery)}%",
            f"Final score: {self.score}",
        ]

        start_y = 245

        for index, line in enumerate(result_lines):
            result_text = normal_font.render(
                line,
                True,
                WHITE
            )

            screen.blit(
                result_text,
                result_text.get_rect(
                    center=(
                        SCREEN_WIDTH // 2,
                        start_y + index * 38
                    )
                )
            )

        mouse_position = pygame.mouse.get_pos()

        self.play_again_button.update(mouse_position)
        self.win_menu_button.update(mouse_position)

        self.play_again_button.draw()
        self.win_menu_button.draw()

    # =====================================================
    # EVENT HANDLING
    # =====================================================

    def handle_menu_events(self, event):
        if self.easy_button.was_clicked(event):
            self.start_new_game("Easy")

        elif self.medium_button.was_clicked(event):
            self.start_new_game("Medium")

        elif self.hard_button.was_clicked(event):
            self.start_new_game("Hard")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.start_new_game("Easy")

            elif event.key == pygame.K_2:
                self.start_new_game("Medium")

            elif event.key == pygame.K_3:
                self.start_new_game("Hard")

    def handle_playing_events(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.move_player(-1, 0)

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.move_player(1, 0)

        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.move_player(0, -1)

        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.move_player(0, 1)

        elif event.key == pygame.K_p:
            self.pause_game()

        elif event.key == pygame.K_ESCAPE:
            self.pause_game()

        elif event.key == pygame.K_r:
            self.start_new_game(self.difficulty_name)

        elif event.key == pygame.K_m:
            self.state = "menu"

    def handle_pause_events(self, event):
        if self.resume_button.was_clicked(event):
            self.resume_game()

        elif self.menu_button.was_clicked(event):
            self.state = "menu"

        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_p,
                pygame.K_ESCAPE
            ):
                self.resume_game()

            elif event.key == pygame.K_m:
                self.state = "menu"

    def handle_win_events(self, event):
        if self.play_again_button.was_clicked(event):
            self.start_new_game(self.difficulty_name)

        elif self.win_menu_button.was_clicked(event):
            self.state = "menu"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.start_new_game(self.difficulty_name)

            elif event.key in (
                pygame.K_m,
                pygame.K_ESCAPE
            ):
                self.state = "menu"

    def handle_event(self, event):
        if self.state == "menu":
            self.handle_menu_events(event)

        elif self.state == "playing":
            self.handle_playing_events(event)

        elif self.state == "paused":
            self.handle_pause_events(event)

        elif self.state == "won":
            self.handle_win_events(event)

    # =====================================================
    # UPDATE AND DRAW
    # =====================================================

    def update(self, delta_time):
        self.animation_time += delta_time

        if self.state == "playing":
            self.update_battery(delta_time)

    def draw_game(self):
        screen.fill(BACKGROUND)

        self.draw_maze()
        self.draw_battery_pickups()
        self.draw_exit()
        self.draw_player()
        self.draw_hud()
        self.draw_low_battery_warning()

    def draw(self):
        if self.state == "menu":
            self.draw_menu()

        elif self.state == "playing":
            self.draw_game()

        elif self.state == "paused":
            self.draw_game()
            self.draw_pause_screen()

        elif self.state == "won":
            self.draw_game()
            self.draw_win_screen()


# =========================================================
# MAIN LOOP
# =========================================================

game = InvisibleMazeGame()

running = True

while running:
    delta_time = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        else:
            game.handle_event(event)

    game.update(delta_time)
    game.draw()

    pygame.display.flip()


pygame.quit()
sys.exit()