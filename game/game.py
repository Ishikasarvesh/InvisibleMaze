import math
import sys
import time

import pygame

from game.battery import BatteryManager
from game.maze import Maze
from game.particles import ParticleManager
from game.player import Player
from game.settings import (
    BACKGROUND,
    DIFFICULTY_SETTINGS,
    EXIT_COLOR,
    GAME_STATE_MENU,
    GAME_STATE_PAUSED,
    GAME_STATE_PLAYING,
    GAME_STATE_WON,
    GREEN_LIGHT,
    HUD_HEIGHT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    create_fonts,
)
from ui.hud import HUD
from ui.menu import MainMenu
from ui.pause_screen import PauseScreen
from ui.result_screen import ResultScreen
from ui.transitions import TransitionManager


class InvisibleMazeGame:
    """
    Main controller for Invisible Maze.

    This class connects:

    - Main menu
    - Difficulty selection
    - Maze generation
    - Player movement
    - Battery system
    - Torch visibility
    - Particle effects
    - HUD
    - Pause screen
    - Result screen
    - Screen transitions
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Invisible Maze")

        self.screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        )

        self.clock = pygame.time.Clock()

        self.running = True

        self.fonts = create_fonts()

        # -------------------------------------------------
        # Main game state
        # -------------------------------------------------

        self.game_state = GAME_STATE_MENU
        self.previous_game_state = GAME_STATE_MENU

        self.selected_difficulty = "Easy"
        self.difficulty_config = None

        # -------------------------------------------------
        # Game objects
        # -------------------------------------------------

        self.maze = None
        self.player = None
        self.battery_manager = None

        # -------------------------------------------------
        # Shared systems
        # -------------------------------------------------

        self.particle_manager = ParticleManager(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        self.hud = HUD(self.fonts)

        self.main_menu = MainMenu(
            self.fonts,
            self.particle_manager,
        )

        self.pause_screen = PauseScreen(
            self.fonts
        )

        self.result_screen = ResultScreen(
            self.fonts,
            self.particle_manager,
        )

        self.transition_manager = (
            TransitionManager()
        )

        # -------------------------------------------------
        # Game values
        # -------------------------------------------------

        self.battery_percentage = 100.0
        self.maximum_battery = 100.0

        self.moves = 0
        self.score = 0
        self.final_score = 0

        self.elapsed_time = 0.0
        self.game_start_time = 0.0

        self.pause_start_time = 0.0
        self.total_paused_time = 0.0

        self.exit_particle_timer = 0.0
        self.exit_particle_interval = 0.08

        self.win_animation_started = False

        # Prevents movement from being repeated too quickly.
        self.movement_cooldown = 0.0
        self.movement_delay = 0.08

    # =====================================================
    # GAME CREATION
    # =====================================================

    def start_game(self, difficulty):
        """
        Starts a completely new maze using the selected
        difficulty.
        """

        if difficulty not in DIFFICULTY_SETTINGS:
            difficulty = "Easy"

        self.selected_difficulty = difficulty

        self.difficulty_config = (
            DIFFICULTY_SETTINGS[difficulty]
        )

        rows = self.get_setting(
            "rows",
            17,
        )

        cols = self.get_setting(
            "cols",
            rows,
        )

        battery_count = self.get_setting(
            "battery_count",
            5,
        )

        battery_restore = self.get_setting(
            "battery_restore",
            25,
        )

        self.maze = Maze(
            rows=rows,
            cols=cols,
        )

        start_row, start_col = (
            self.maze.start_position
        )

        self.player = Player(
            row=start_row,
            col=start_col,
            maze=self.maze,
        )

        self.battery_manager = BatteryManager(
            maze=self.maze,
            pickup_count=battery_count,
            restore_amount=battery_restore,
        )

        self.battery_percentage = 100.0

        self.moves = 0
        self.score = 0
        self.final_score = 0

        self.elapsed_time = 0.0
        self.game_start_time = time.time()

        self.total_paused_time = 0.0
        self.pause_start_time = 0.0

        self.exit_particle_timer = 0.0
        self.win_animation_started = False

        self.movement_cooldown = 0.0

        self.particle_manager.clear()

        self.hud.displayed_battery.snap(
            100
        )

        self.hud.displayed_score.snap(
            0
        )

        self.game_state = GAME_STATE_PLAYING

        self.hud.show_notification(
            f"{difficulty} maze started"
        )

    def restart_game(self):
        """
        Restarts the current difficulty.
        """

        self.start_game(
            self.selected_difficulty
        )

    def open_main_menu(self):
        """
        Returns to the main menu.
        """

        self.game_state = GAME_STATE_MENU

        self.maze = None
        self.player = None
        self.battery_manager = None

        self.particle_manager.clear()

    def get_setting(
        self,
        key,
        default_value,
    ):
        """
        Safely reads one difficulty setting.

        This keeps the game working even when a setting
        has a slightly different name.
        """

        if self.difficulty_config is None:
            return default_value

        return self.difficulty_config.get(
            key,
            default_value,
        )

    # =====================================================
    # EVENT HANDLING
    # =====================================================

    def handle_events(self):
        """
        Reads and routes all Pygame events.
        """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if (
                self.transition_manager.is_active()
            ):
                continue

            if self.game_state == GAME_STATE_MENU:
                self.handle_menu_event(event)

            elif (
                self.game_state
                == GAME_STATE_PLAYING
            ):
                self.handle_playing_event(event)

            elif (
                self.game_state
                == GAME_STATE_PAUSED
            ):
                self.handle_pause_event(event)

            elif self.game_state == GAME_STATE_WON:
                self.handle_result_event(event)

    def handle_menu_event(self, event):
        """
        Handles main-menu buttons and shortcuts.
        """

        action = self.main_menu.handle_event(
            event
        )

        if action is None:
            return

        action_name, action_value = action

        if action_name == "start":
            self.transition_manager.start_circle(
                callback=lambda: self.start_game(
                    action_value
                ),
                center=(
                    SCREEN_WIDTH // 2,
                    SCREEN_HEIGHT // 2,
                ),
            )

        elif action_name == "settings":
            self.hud.show_notification(
                "Settings screen will be added later"
            )

    def handle_playing_event(self, event):
        """
        Handles controls while playing.
        """

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (
            pygame.K_p,
            pygame.K_ESCAPE,
        ):
            self.pause_game()
            return

        if event.key == pygame.K_r:
            self.transition_manager.start_fade(
                callback=self.restart_game
            )
            return

        if event.key == pygame.K_m:
            self.transition_manager.start_fade(
                callback=self.open_main_menu
            )
            return

        direction = self.get_direction_from_key(
            event.key
        )

        if direction is not None:
            self.try_move_player(direction)

    def handle_pause_event(self, event):
        """
        Handles pause-screen actions.
        """

        action = self.pause_screen.handle_event(
            event
        )

        if action == "continue":
            self.resume_game()

        elif action == "restart":
            self.transition_manager.start_fade(
                callback=self.restart_game
            )

        elif action == "menu":
            self.transition_manager.start_fade(
                callback=self.open_main_menu
            )

    def handle_result_event(self, event):
        """
        Handles the victory screen.
        """

        action = self.result_screen.handle_event(
            event
        )

        if action == "play_again":
            self.transition_manager.start_fade(
                callback=self.restart_game
            )

        elif action == "menu":
            self.transition_manager.start_fade(
                callback=self.open_main_menu
            )

    def get_direction_from_key(self, key):
        """
        Converts keyboard input into a grid direction.

        Returns:
            (row_change, column_change)
        """

        direction_keys = {
            pygame.K_UP: (-1, 0),
            pygame.K_w: (-1, 0),

            pygame.K_DOWN: (1, 0),
            pygame.K_s: (1, 0),

            pygame.K_LEFT: (0, -1),
            pygame.K_a: (0, -1),

            pygame.K_RIGHT: (0, 1),
            pygame.K_d: (0, 1),
        }

        return direction_keys.get(key)

    # =====================================================
    # PLAYER MOVEMENT
    # =====================================================

    def try_move_player(self, direction):
        """
        Tries to move the player by one maze cell.
        """

        if self.player is None:
            return

        if self.movement_cooldown > 0:
            return

        if self.player.is_moving:
            return

        row_change, col_change = direction

        target_row = (
            self.player.row
            + row_change
        )

        target_col = (
            self.player.col
            + col_change
        )

        if self.maze.is_path(
            target_row,
            target_col,
        ):
            moved = self.player.move(
                row_change,
                col_change,
            )

            if moved:
                self.moves += 1

                self.movement_cooldown = (
                    self.movement_delay
                )

                self.maze.mark_visited(
                    self.player.row,
                    self.player.col,
                )

                self.check_battery_collection()

                self.check_win_condition()

        else:
            self.player.hit_wall(direction)

            player_x, player_y = (
                self.player.get_center()
            )

            self.particle_manager.create_wall_hit_sparks(
                player_x,
                player_y,
                direction,
            )

    def check_battery_collection(self):
        """
        Checks whether the player's current cell contains
        a battery pickup.
        """

        if self.battery_manager is None:
            return

        restored_amount = (
            self.battery_manager.collect_at(
                self.player.row,
                self.player.col,
            )
        )

        if restored_amount <= 0:
            return

        previous_battery = (
            self.battery_percentage
        )

        self.battery_percentage = min(
            self.maximum_battery,
            self.battery_percentage
            + restored_amount,
        )

        actual_restored = int(
            self.battery_percentage
            - previous_battery
        )

        center_x, center_y = (
            self.maze.get_cell_center(
                self.player.row,
                self.player.col,
            )
        )

        self.particle_manager.create_battery_burst(
            center_x,
            center_y,
        )

        self.hud.show_notification(
            f"Battery collected: +{actual_restored}%"
        )

    # =====================================================
    # PAUSE SYSTEM
    # =====================================================

    def pause_game(self):
        """
        Pauses the game and stores the pause start time.
        """

        if self.game_state != GAME_STATE_PLAYING:
            return

        self.game_state = GAME_STATE_PAUSED

        self.pause_start_time = time.time()

        self.pause_screen.open()

    def resume_game(self):
        """
        Resumes the game and excludes paused time from
        the final timer.
        """

        if self.game_state != GAME_STATE_PAUSED:
            return

        if self.pause_start_time > 0:
            paused_duration = (
                time.time()
                - self.pause_start_time
            )

            self.total_paused_time += (
                paused_duration
            )

        self.pause_start_time = 0.0

        self.game_state = GAME_STATE_PLAYING

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, delta_time):
        """
        Updates the active game screen.
        """

        self.transition_manager.update(
            delta_time
        )

        self.particle_manager.update(
            delta_time,
            update_fireflies=True,
        )

        if self.game_state == GAME_STATE_MENU:
            self.update_menu(delta_time)

        elif (
            self.game_state
            == GAME_STATE_PLAYING
        ):
            self.update_playing(delta_time)

        elif (
            self.game_state
            == GAME_STATE_PAUSED
        ):
            self.update_paused(delta_time)

        elif self.game_state == GAME_STATE_WON:
            self.update_won(delta_time)

    def update_menu(self, delta_time):
        """
        Updates the animated main menu.
        """

        self.main_menu.update(delta_time)

    def update_playing(self, delta_time):
        """
        Updates gameplay logic.
        """

        if (
            self.maze is None
            or self.player is None
        ):
            return

        self.movement_cooldown = max(
            0,
            self.movement_cooldown
            - delta_time,
        )

        self.player.update(delta_time)

        self.battery_manager.update(
            delta_time
        )

        self.update_elapsed_time()
        self.update_battery(delta_time)
        self.update_score()
        self.update_exit_particles(delta_time)

        player_x, player_y = (
            self.player.get_center()
        )

        if self.player.is_moving:
            self.particle_manager.create_player_trail(
                player_x,
                player_y,
            )

        remaining_batteries = (
            self.battery_manager
            .get_remaining_count()
        )

        self.hud.update(
            delta_time=delta_time,
            battery=self.battery_percentage,
            score=self.score,
        )

        if self.battery_percentage <= 0:
            self.battery_percentage = 0

            self.hud.show_notification(
                "Your torch has completely faded"
            )

        self.check_win_condition()

    def update_paused(self, delta_time):
        """
        Updates only pause-screen UI.

        The player, timer and battery are not updated.
        """

        self.pause_screen.update(
            delta_time
        )

    def update_won(self, delta_time):
        """
        Updates the victory screen.
        """

        self.result_screen.update(
            delta_time
        )

    # =====================================================
    # TIMER AND BATTERY
    # =====================================================

    def update_elapsed_time(self):
        """
        Calculates active gameplay time.
        """

        current_time = time.time()

        self.elapsed_time = (
            current_time
            - self.game_start_time
            - self.total_paused_time
        )

        self.elapsed_time = max(
            0,
            self.elapsed_time,
        )

    def update_battery(self, delta_time):
        """
        Drains torch energy while the game is active.
        """

        drain_rate = self.get_setting(
            "battery_drain",
            self.get_setting(
                "drain_rate",
                1.0,
            ),
        )

        self.battery_percentage -= (
            drain_rate
            * delta_time
        )

        self.battery_percentage = max(
            0,
            min(
                self.maximum_battery,
                self.battery_percentage,
            ),
        )

    def get_visibility_radius(self):
        """
        Calculates visibility based on difficulty and
        remaining torch battery.
        """

        base_radius = self.get_setting(
            "visibility_radius",
            self.get_setting(
                "torch_radius",
                4,
            ),
        )

        minimum_radius = self.get_setting(
            "minimum_visibility",
            1,
        )

        battery_ratio = (
            self.battery_percentage
            / self.maximum_battery
        )

        dynamic_radius = int(
            minimum_radius
            + (
                base_radius
                - minimum_radius
            )
            * battery_ratio
        )

        if self.battery_percentage <= 0:
            return minimum_radius

        return max(
            minimum_radius,
            dynamic_radius,
        )

    # =====================================================
    # SCORE SYSTEM
    # =====================================================

    def update_score(self):
        """
        Updates the live score shown in the HUD.
        """

        difficulty_multiplier = (
            self.get_difficulty_multiplier()
        )

        base_score = (
            1000
            * difficulty_multiplier
        )

        battery_bonus = (
            self.battery_percentage
            * 5
            * difficulty_multiplier
        )

        time_penalty = (
            self.elapsed_time
            * 2
        )

        move_penalty = (
            self.moves
            * 3
        )

        self.score = max(
            0,
            int(
                base_score
                + battery_bonus
                - time_penalty
                - move_penalty
            ),
        )

    def calculate_final_score(self):
        """
        Calculates the score displayed after winning.
        """

        difficulty_multiplier = (
            self.get_difficulty_multiplier()
        )

        completion_bonus = (
            1500
            * difficulty_multiplier
        )

        battery_bonus = (
            self.battery_percentage
            * 10
            * difficulty_multiplier
        )

        speed_bonus = max(
            0,
            1000
            - self.elapsed_time * 5,
        )

        efficiency_bonus = max(
            0,
            800
            - self.moves * 4,
        )

        return max(
            0,
            int(
                completion_bonus
                + battery_bonus
                + speed_bonus
                + efficiency_bonus
            ),
        )

    def get_difficulty_multiplier(self):
        """
        Returns the score multiplier for each difficulty.
        """

        multipliers = {
            "Easy": 1.0,
            "Medium": 1.5,
            "Hard": 2.0,
        }

        return multipliers.get(
            self.selected_difficulty,
            1.0,
        )

    # =====================================================
    # EXIT AND WIN SYSTEM
    # =====================================================

    def update_exit_particles(
        self,
        delta_time,
    ):
        """
        Continuously creates particles around the exit.
        """

        self.exit_particle_timer -= (
            delta_time
        )

        if self.exit_particle_timer > 0:
            return

        self.exit_particle_timer = (
            self.exit_particle_interval
        )

        exit_row, exit_col = (
            self.maze.exit_position
        )

        exit_x, exit_y = (
            self.maze.get_cell_center(
                exit_row,
                exit_col,
            )
        )

        self.particle_manager.create_exit_particle(
            exit_x,
            exit_y,
            radius=max(
                10,
                self.maze.cell_size // 2,
            ),
        )

    def check_win_condition(self):
        """
        Checks whether the player reached the exit.
        """

        if self.game_state != GAME_STATE_PLAYING:
            return

        player_position = (
            self.player.row,
            self.player.col,
        )

        if (
            player_position
            != self.maze.exit_position
        ):
            return

        self.complete_game()

    def complete_game(self):
        """
        Finishes the game and opens the result screen.
        """

        if self.win_animation_started:
            return

        self.win_animation_started = True

        self.update_elapsed_time()

        self.final_score = (
            self.calculate_final_score()
        )

        exit_row, exit_col = (
            self.maze.exit_position
        )

        exit_x, exit_y = (
            self.maze.get_cell_center(
                exit_row,
                exit_col,
            )
        )

        self.particle_manager.create_win_burst(
            exit_x,
            exit_y,
        )

        self.result_screen.open(
            difficulty=(
                self.selected_difficulty
            ),
            moves=self.moves,
            elapsed_seconds=int(
                self.elapsed_time
            ),
            battery=(
                self.battery_percentage
            ),
            score=self.final_score,
        )

        self.game_state = GAME_STATE_WON

    # =====================================================
    # DRAWING
    # =====================================================

    def draw(self):
        """
        Draws the current screen.
        """

        self.screen.fill(BACKGROUND)

        if self.game_state == GAME_STATE_MENU:
            self.draw_menu()

        elif (
            self.game_state
            == GAME_STATE_PLAYING
        ):
            self.draw_gameplay()

        elif (
            self.game_state
            == GAME_STATE_PAUSED
        ):
            self.draw_gameplay()
            self.pause_screen.draw(
                self.screen
            )

        elif self.game_state == GAME_STATE_WON:
            self.draw_result()

        self.transition_manager.draw(
            self.screen
        )

        pygame.display.flip()

    def draw_menu(self):
        """
        Draws the main menu.
        """

        self.main_menu.draw(
            self.screen
        )

    def draw_gameplay(self):
        """
        Draws the maze, exit, pickups, player and HUD.
        """

        if (
            self.maze is None
            or self.player is None
        ):
            return

        self.screen.fill(BACKGROUND)

        visibility_radius = (
            self.get_visibility_radius()
        )

        self.maze.draw(
            surface=self.screen,
            player_row=self.player.row,
            player_col=self.player.col,
            visibility_radius=visibility_radius,
        )

        self.draw_exit(
            visibility_radius
        )

        self.battery_manager.draw(
            surface=self.screen,
            player_row=self.player.row,
            player_col=self.player.col,
            visibility_radius=visibility_radius,
        )

        self.particle_manager.draw_particles(
            self.screen
        )

        self.player.draw_torch_glow(
            self.screen,
            battery_percentage=(
                self.battery_percentage
            ),
            visibility_radius=(
                visibility_radius
            ),
        )

        self.player.draw(
            self.screen
        )

        remaining_batteries = (
            self.battery_manager
            .get_remaining_count()
        )

        self.hud.draw(
            surface=self.screen,
            difficulty=(
                self.selected_difficulty
            ),
            moves=self.moves,
            elapsed_seconds=int(
                self.elapsed_time
            ),
            battery=(
                self.battery_percentage
            ),
            score=self.score,
            remaining_batteries=(
                remaining_batteries
            ),
        )

    def draw_exit(
        self,
        visibility_radius,
    ):
        """
        Draws an animated exit portal when visible.
        """

        exit_row, exit_col = (
            self.maze.exit_position
        )

        is_visible = (
            self.maze.is_cell_visible(
                exit_row,
                exit_col,
                self.player.row,
                self.player.col,
                visibility_radius,
            )
        )

        if not is_visible:
            return

        center_x, center_y = (
            self.maze.get_cell_center(
                exit_row,
                exit_col,
            )
        )

        pulse_value = (
            math.sin(
                pygame.time.get_ticks()
                * 0.006
            )
            + 1
        ) / 2

        outer_radius = int(
            self.maze.cell_size
            * (
                0.35
                + pulse_value * 0.08
            )
        )

        inner_radius = max(
            4,
            int(
                outer_radius * 0.55
            ),
        )

        glow_surface = pygame.Surface(
            self.screen.get_size(),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            glow_surface,
            (
                GREEN_LIGHT[0],
                GREEN_LIGHT[1],
                GREEN_LIGHT[2],
                28,
            ),
            (
                center_x,
                center_y,
            ),
            outer_radius + 16,
        )

        pygame.draw.circle(
            glow_surface,
            (
                EXIT_COLOR[0],
                EXIT_COLOR[1],
                EXIT_COLOR[2],
                55,
            ),
            (
                center_x,
                center_y,
            ),
            outer_radius + 7,
        )

        self.screen.blit(
            glow_surface,
            (0, 0),
        )

        pygame.draw.circle(
            self.screen,
            EXIT_COLOR,
            (
                center_x,
                center_y,
            ),
            outer_radius,
            width=max(
                2,
                self.maze.cell_size // 10,
            ),
        )

        pygame.draw.circle(
            self.screen,
            GREEN_LIGHT,
            (
                center_x,
                center_y,
            ),
            inner_radius,
        )

    def draw_result(self):
        """
        Draws the victory screen.
        """

        self.result_screen.draw(
            self.screen
        )

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def run(self):
        """
        Runs the main Pygame loop.
        """

        while self.running:
            delta_time = (
                self.clock.tick(60)
                / 1000.0
            )

            delta_time = min(
                delta_time,
                0.05,
            )

            self.handle_events()
            self.update(delta_time)
            self.draw()

        self.close()

    def close(self):
        """
        Safely closes Pygame.
        """

        pygame.quit()
        sys.exit()