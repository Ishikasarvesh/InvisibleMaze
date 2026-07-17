import inspect
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
    MAZE_BOTTOM_MARGIN,
    MAZE_SIDE_MARGIN,
    MAZE_TOP_MARGIN,
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
    """Main controller for the Invisible Maze game."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Invisible Maze")

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        self.clock = pygame.time.Clock()
        self.running = True
        self.fonts = create_fonts()

        # =====================================================
        # GAME STATE
        # =====================================================

        self.game_state = GAME_STATE_MENU
        self.previous_game_state = GAME_STATE_MENU

        self.selected_difficulty = "Easy"
        self.difficulty_config = None

        # =====================================================
        # GAME OBJECTS
        # =====================================================

        self.maze = None
        self.player = None
        self.battery_manager = None

        # =====================================================
        # SHARED SYSTEMS
        # =====================================================

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

        self.transition_manager = TransitionManager()

        # =====================================================
        # GAME VALUES
        # =====================================================

        self.maximum_battery = 100.0
        self.battery_percentage = 100.0

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
        self.zero_battery_message_shown = False

        self.movement_cooldown = 0.0
        self.movement_delay = 0.08

    # =========================================================
    # GENERAL HELPERS
    # =========================================================

    def get_setting(self, key, default_value):
        """Return one difficulty setting safely."""

        if self.difficulty_config is None:
            return default_value

        return self.difficulty_config.get(
            key,
            default_value,
        )

    @staticmethod
    def get_parameter_names(callable_object):
        """Return parameter names from a class or method."""

        try:
            signature = inspect.signature(
                callable_object
            )

            return [
                name
                for name in signature.parameters
                if name != "self"
            ]

        except (TypeError, ValueError):
            return []

    def show_notification(self, message):
        """Show a HUD notification when supported."""

        if hasattr(self.hud, "show_notification"):
            self.hud.show_notification(message)

    def get_start_position(self):
        """Return the maze starting cell."""

        if self.maze is None:
            return 1, 1

        if hasattr(self.maze, "start_position"):
            position = self.maze.start_position

            if callable(position):
                position = position()

            return tuple(position)

        if (
            hasattr(self.maze, "start_row")
            and hasattr(self.maze, "start_col")
        ):
            return (
                self.maze.start_row,
                self.maze.start_col,
            )

        if hasattr(self.maze, "start"):
            return tuple(self.maze.start)

        return 1, 1

    def get_exit_position(self):
        """Return the maze exit cell."""

        if self.maze is None:
            return 1, 1

        if hasattr(self.maze, "exit_position"):
            position = self.maze.exit_position

            if callable(position):
                position = position()

            return tuple(position)

        if (
            hasattr(self.maze, "exit_row")
            and hasattr(self.maze, "exit_col")
        ):
            return (
                self.maze.exit_row,
                self.maze.exit_col,
            )

        if hasattr(self.maze, "exit"):
            return tuple(self.maze.exit)

        return (
            self.maze.rows - 2,
            self.maze.cols - 2,
        )

    def get_cell_center(self, row, col):
        """Return the screen centre of a maze cell."""
        if self.maze is None:
            return 0, 0
        return self.maze.get_cell_center(row, col)

    def get_player_center(self):
        """Return the player's current screen position."""

        if self.player is None:
            return 0, 0

        if hasattr(self.player, "get_center"):
            return self.player.get_center()

        if (
            hasattr(self.player, "x")
            and hasattr(self.player, "y")
        ):
            return (
                int(self.player.x),
                int(self.player.y),
            )

        return self.get_cell_center(
            self.player.row,
            self.player.col,
        )

    # =========================================================
    # OBJECT CREATION
    # =========================================================

    def create_maze(
        self,
        rows,
        cols,
        cell_size,
        start_x,
        start_y,
    ):
        """Create Maze using its confirmed constructor."""

        return Maze(
            rows=rows,
            cols=cols,
            cell_size=cell_size,
            start_x=start_x,
            start_y=start_y,
        )

    def create_player(
        self,
        start_row,
        start_col,
    ):
        """
        Create Player using the actual constructor.

        The current Player class expects:
        Player(maze, start_row, start_col)
        """
        return Player(
            self.maze,
            start_row,
            start_col,
        )

    def create_battery_manager(
        self,
        battery_count,
        battery_restore,
    ):
        """Create BatteryManager according to its parameters."""
        return BatteryManager(
            self.maze,
            battery_count,
            battery_restore,
        )

    # =========================================================
    # START, RESTART AND MENU
    # =========================================================

    def start_game(self, difficulty):
        """Create and start a new maze."""

        if difficulty not in DIFFICULTY_SETTINGS:
            difficulty = "Easy"

        self.selected_difficulty = difficulty
        self.difficulty_config = (
            DIFFICULTY_SETTINGS[difficulty]
        )

        rows = int(
            self.get_setting("rows", 17)
        )

        cols = int(
            self.get_setting("cols", rows)
        )

        battery_count = int(
            self.get_setting(
                "battery_count",
                self.get_setting(
                    "battery_pickups",
                    5,
                ),
            )
        )

        battery_restore = float(
            self.get_setting(
                "battery_restore",
                25,
            )
        )

        starting_battery = float(
            self.get_setting(
                "starting_battery",
                100,
            )
        )

        # =====================================================
        # MAZE SIZE AND POSITION
        # =====================================================

        available_width = (
            SCREEN_WIDTH
            - MAZE_SIDE_MARGIN * 2
        )

        available_height = (
            SCREEN_HEIGHT
            - MAZE_TOP_MARGIN
            - MAZE_BOTTOM_MARGIN
        )

        cell_size = min(
            available_width // cols,
            available_height // rows,
        )

        cell_size = max(8, cell_size)

        maze_pixel_width = cols * cell_size
        maze_pixel_height = rows * cell_size

        maze_start_x = (
            SCREEN_WIDTH - maze_pixel_width
        ) // 2

        maze_start_y = (
            MAZE_TOP_MARGIN
            + (
                available_height
                - maze_pixel_height
            )
            // 2
        )

        # =====================================================
        # CREATE GAME OBJECTS
        # =====================================================

        self.maze = self.create_maze(
            rows,
            cols,
            cell_size,
            maze_start_x,
            maze_start_y,
        )

        start_row, start_col = (
            self.get_start_position()
        )

        self.player = self.create_player(
            start_row,
            start_col,
        )

        self.battery_manager = (
            self.create_battery_manager(
                battery_count,
                battery_restore,
            )
        )

        # =====================================================
        # RESET GAME VALUES
        # =====================================================

        self.maximum_battery = 100.0

        self.battery_percentage = max(
            0.0,
            min(
                self.maximum_battery,
                starting_battery,
            ),
        )

        self.moves = 0
        self.score = 0
        self.final_score = 0

        self.elapsed_time = 0.0
        self.game_start_time = time.time()

        self.pause_start_time = 0.0
        self.total_paused_time = 0.0

        self.exit_particle_timer = 0.0
        self.win_animation_started = False
        self.zero_battery_message_shown = False

        self.movement_cooldown = 0.0

        if hasattr(
            self.particle_manager,
            "clear",
        ):
            self.particle_manager.clear()

        self.reset_hud_values()

        self.game_state = GAME_STATE_PLAYING

        self.show_notification(
            f"{difficulty} maze started"
        )

    def reset_hud_values(self):
        """Reset animated HUD values."""

        if hasattr(
            self.hud,
            "displayed_battery",
        ):
            animated_value = (
                self.hud.displayed_battery
            )

            if hasattr(animated_value, "snap"):
                animated_value.snap(
                    self.battery_percentage
                )

            elif hasattr(animated_value, "value"):
                animated_value.value = (
                    self.battery_percentage
                )

        if hasattr(
            self.hud,
            "displayed_score",
        ):
            animated_value = (
                self.hud.displayed_score
            )

            if hasattr(animated_value, "snap"):
                animated_value.snap(0)

            elif hasattr(animated_value, "value"):
                animated_value.value = 0

    def restart_game(self):
        """Restart the current difficulty."""

        self.start_game(
            self.selected_difficulty
        )

    def open_main_menu(self):
        """Return to the main menu."""

        self.game_state = GAME_STATE_MENU

        self.maze = None
        self.player = None
        self.battery_manager = None

        if hasattr(
            self.particle_manager,
            "clear",
        ):
            self.particle_manager.clear()

    # =========================================================
    # TRANSITIONS
    # =========================================================

    def transition_is_active(self):
        """Check whether a transition is running."""

        if hasattr(
            self.transition_manager,
            "is_active",
        ):
            return self.transition_manager.is_active()

        if hasattr(
            self.transition_manager,
            "current_transition",
        ):
            return (
                self.transition_manager
                .current_transition
                is not None
            )

        return False

    def start_transition(
        self,
        callback,
        transition_type="fade",
    ):
        """Start a screen transition safely."""

        if (
            transition_type == "circle"
            and hasattr(
                self.transition_manager,
                "start_circle",
            )
        ):
            self.transition_manager.start_circle(
                callback=callback,
                center=(
                    SCREEN_WIDTH // 2,
                    SCREEN_HEIGHT // 2,
                ),
            )

            return

        if hasattr(
            self.transition_manager,
            "start_fade",
        ):
            self.transition_manager.start_fade(
                callback=callback
            )

            return

        callback()

    # =========================================================
    # EVENTS
    # =========================================================

    def handle_events(self):
        """Handle Pygame events."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if self.transition_is_active():
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
        """Handle main-menu events."""

        action = self.main_menu.handle_event(
            event
        )

        if action is None:
            return

        if isinstance(action, tuple):
            action_name = action[0]

            action_value = (
                action[1]
                if len(action) > 1
                else None
            )

        else:
            action_name = action
            action_value = None

        normalized_action = str(
            action_name
        ).lower()

        if normalized_action == "start":
            difficulty = (
                action_value
                if action_value
                else "Easy"
            )

            self.start_transition(
                callback=lambda selected=difficulty:
                self.start_game(selected),
                transition_type="circle",
            )

        elif normalized_action in {
            "easy",
            "medium",
            "hard",
        }:
            difficulty = (
                normalized_action.capitalize()
            )

            self.start_transition(
                callback=lambda selected=difficulty:
                self.start_game(selected),
                transition_type="circle",
            )

        elif normalized_action == "settings":
            self.show_notification(
                "Settings screen will be added later"
            )

        elif normalized_action in {
            "quit",
            "exit",
        }:
            self.running = False

    def handle_playing_event(self, event):
        """Handle keyboard controls during gameplay."""

        if event.type != pygame.KEYDOWN:
            return

        if event.key in {
            pygame.K_p,
            pygame.K_ESCAPE,
        }:
            self.pause_game()
            return

        if event.key == pygame.K_r:
            self.start_transition(
                callback=self.restart_game,
                transition_type="fade",
            )

            return

        if event.key == pygame.K_m:
            self.start_transition(
                callback=self.open_main_menu,
                transition_type="fade",
            )

            return

        direction = self.get_direction_from_key(
            event.key
        )

        if direction is not None:
            self.try_move_player(direction)

    def handle_pause_event(self, event):
        """Handle pause-screen events."""

        if (
            event.type == pygame.KEYDOWN
            and event.key
            in {
                pygame.K_p,
                pygame.K_ESCAPE,
            }
        ):
            self.resume_game()
            return

        action = self.pause_screen.handle_event(
            event
        )

        if action == "continue":
            self.resume_game()

        elif action == "restart":
            self.start_transition(
                callback=self.restart_game,
                transition_type="fade",
            )

        elif action == "menu":
            self.start_transition(
                callback=self.open_main_menu,
                transition_type="fade",
            )

    def handle_result_event(self, event):
        """Handle victory-screen events."""

        action = self.result_screen.handle_event(
            event
        )

        if action == "play_again":
            self.start_transition(
                callback=self.restart_game,
                transition_type="fade",
            )

        elif action == "menu":
            self.start_transition(
                callback=self.open_main_menu,
                transition_type="fade",
            )

    @staticmethod
    def get_direction_from_key(key):
        """Convert arrow keys or WASD into movement."""

        directions = {
            pygame.K_UP: (-1, 0),
            pygame.K_w: (-1, 0),
            pygame.K_DOWN: (1, 0),
            pygame.K_s: (1, 0),
            pygame.K_LEFT: (0, -1),
            pygame.K_a: (0, -1),
            pygame.K_RIGHT: (0, 1),
            pygame.K_d: (0, 1),
        }

        return directions.get(key)

    # =========================================================
    # PLAYER MOVEMENT
    # =========================================================

    def maze_cell_is_path(self, row, col):
        """Check whether the target cell is walkable."""
        if self.maze is None:
            return False
        return self.maze.is_path(row, col)

    def move_player(self, row_change, col_change):
        """Call Player.try_move using its actual parameters."""
        return self.player.try_move(row_change, col_change)

    def try_move_player(self, direction):
        """Attempt to move the player one cell."""

        if (
            self.player is None
            or self.maze is None
        ):
            return

        if self.movement_cooldown > 0:
            return

        if getattr(
            self.player,
            "is_moving",
            False,
        ):
            return

        row_change, col_change = direction

        target_row = (
            self.player.row + row_change
        )

        target_col = (
            self.player.col + col_change
        )

        if self.maze_cell_is_path(
            target_row,
            target_col,
        ):
            moved = self.move_player(
                row_change,
                col_change,
            )

            if moved is None:
                moved = True

            if not moved:
                return

            self.moves += 1

            self.movement_cooldown = (
                self.movement_delay
            )

            self.mark_player_cell_visited()
            self.check_battery_collection()
            self.check_win_condition()

        else:
            self.handle_wall_collision(
                direction
            )

    def mark_player_cell_visited(self):
        """Mark the player's current maze cell as visited."""

        if hasattr(self.maze, "mark_visited"):
            self.maze.mark_visited(
                self.player.row,
                self.player.col,
            )

        elif hasattr(self.maze, "visited_cells"):
            self.maze.visited_cells.add(
                (
                    self.player.row,
                    self.player.col,
                )
            )

    def handle_wall_collision(self, direction):
        """Animate and show particles for a wall hit."""
        if hasattr(self.player, "play_wall_hit_animation"):
            self.player.play_wall_hit_animation()

        player_x, player_y = self.get_player_center()
        self.particle_manager.create_wall_hit_sparks(
            player_x,
            player_y,
            direction,
        )

    # =========================================================
    # BATTERY PICKUPS
    # =========================================================

    def collect_battery_at_player(self):
        """Call the battery collection method."""
        if self.battery_manager is None:
            return 0
        return self.battery_manager.collect_at(
            self.player.row,
            self.player.col,
        )

    def check_battery_collection(self):
        """Restore energy when a battery is collected."""

        restored_amount = (
            self.collect_battery_at_player()
        )

        try:
            restored_amount = float(
                restored_amount
            )

        except (TypeError, ValueError):
            restored_amount = 0

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
            self.get_cell_center(
                self.player.row,
                self.player.col,
            )
        )

        if hasattr(
            self.particle_manager,
            "create_battery_burst",
        ):
            self.particle_manager.create_battery_burst(
                center_x,
                center_y,
            )

        self.show_notification(
            f"Battery collected: +{actual_restored}%"
        )

    def get_remaining_battery_count(self):
        """Return the number of uncollected batteries."""
        if self.battery_manager is None:
            return 0
        return self.battery_manager.get_remaining_count()

    # =========================================================
    # PAUSE
    # =========================================================

    def pause_game(self):
        """Pause the game."""

        if (
            self.game_state
            != GAME_STATE_PLAYING
        ):
            return

        self.game_state = GAME_STATE_PAUSED
        self.pause_start_time = time.time()

        if hasattr(self.pause_screen, "open"):
            self.pause_screen.open()

    def resume_game(self):
        """Resume the game."""

        if (
            self.game_state
            != GAME_STATE_PAUSED
        ):
            return

        if self.pause_start_time > 0:
            self.total_paused_time += (
                time.time()
                - self.pause_start_time
            )

        self.pause_start_time = 0.0
        self.game_state = GAME_STATE_PLAYING

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, delta_time):
        """Update all active game systems."""

        if hasattr(
            self.transition_manager,
            "update",
        ):
            self.transition_manager.update(
                delta_time
            )

        self.update_particles(delta_time)

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

    def update_particles(self, delta_time):
        """Update the particle system."""

        if not hasattr(
            self.particle_manager,
            "update",
        ):
            return

        update_method = (
            self.particle_manager.update
        )

        parameter_names = (
            self.get_parameter_names(
                update_method
            )
        )

        if "update_fireflies" in parameter_names:
            update_method(
                delta_time,
                update_fireflies=True,
            )

        else:
            update_method(delta_time)

    def update_menu(self, delta_time):
        """Update menu animations."""

        if hasattr(self.main_menu, "update"):
            self.main_menu.update(delta_time)

    def update_playing(self, delta_time):
        """Update active gameplay."""

        if (
            self.maze is None
            or self.player is None
        ):
            return

        self.movement_cooldown = max(
            0.0,
            self.movement_cooldown
            - delta_time,
        )

        if hasattr(self.player, "update"):
            self.player.update(delta_time)

        if (
            self.battery_manager is not None
            and hasattr(
                self.battery_manager,
                "update",
            )
        ):
            self.battery_manager.update(
                delta_time
            )

        self.update_elapsed_time()
        self.update_battery(delta_time)
        self.update_score()
        self.update_exit_particles(
            delta_time
        )

        if getattr(
            self.player,
            "is_moving",
            False,
        ):
            self.create_player_trail()

        self.update_hud(delta_time)

        if (
            self.battery_percentage <= 0
            and not
            self.zero_battery_message_shown
        ):
            self.zero_battery_message_shown = True

            self.show_notification(
                "Your torch has completely faded"
            )

        elif self.battery_percentage > 0:
            self.zero_battery_message_shown = (
                False
            )

        self.check_win_condition()

    def create_player_trail(self):
        """Create particles behind the moving player."""

        if not hasattr(
            self.particle_manager,
            "create_player_trail",
        ):
            return

        player_x, player_y = (
            self.get_player_center()
        )

        self.particle_manager.create_player_trail(
            player_x,
            player_y,
        )

    def update_hud(self, delta_time):
        """Update animated HUD values."""
        if self.hud is not None:
            self.hud.update(
                delta_time,
                self.battery_percentage,
                self.score,
            )

    def update_paused(self, delta_time):
        """Update pause-screen animations."""

        if hasattr(self.pause_screen, "update"):
            self.pause_screen.update(delta_time)

    def update_won(self, delta_time):
        """Update result-screen animations."""

        if hasattr(self.result_screen, "update"):
            self.result_screen.update(
                delta_time
            )

    def update_elapsed_time(self):
        """Calculate active gameplay time."""

        if self.game_start_time <= 0:
            self.elapsed_time = 0.0
            return

        self.elapsed_time = max(
            0.0,
            time.time()
            - self.game_start_time
            - self.total_paused_time,
        )

    def update_battery(self, delta_time):
        """Drain the torch battery."""

        drain_rate = float(
            self.get_setting(
                "battery_drain",
                1.0,
            )
        )

        self.battery_percentage -= (
            drain_rate * delta_time
        )

        self.battery_percentage = max(
            0.0,
            min(
                self.maximum_battery,
                self.battery_percentage,
            ),
        )

    def get_visibility_radius(self):
        """Calculate visibility from battery power."""

        maximum_visibility = int(
            self.get_setting(
                "visibility_radius",
                self.get_setting(
                    "maximum_visibility",
                    4,
                ),
            )
        )

        minimum_visibility = int(
            self.get_setting(
                "minimum_visibility",
                1,
            )
        )

        if self.maximum_battery <= 0:
            return minimum_visibility

        battery_ratio = (
            self.battery_percentage
            / self.maximum_battery
        )

        dynamic_radius = round(
            minimum_visibility
            + (
                maximum_visibility
                - minimum_visibility
            )
            * battery_ratio
        )

        return max(
            minimum_visibility,
            min(
                maximum_visibility,
                dynamic_radius,
            ),
        )

    # =========================================================
    # SCORE
    # =========================================================

    def get_difficulty_multiplier(self):
        """Return the difficulty score multiplier."""

        return {
            "Easy": 1.0,
            "Medium": 1.5,
            "Hard": 2.0,
        }.get(
            self.selected_difficulty,
            1.0,
        )

    def update_score(self):
        """Update the live score."""

        multiplier = (
            self.get_difficulty_multiplier()
        )

        score_bonus = float(
            self.get_setting(
                "score_bonus",
                1000 * multiplier,
            )
        )

        battery_bonus = (
            self.battery_percentage
            * 5
            * multiplier
        )

        time_penalty = (
            self.elapsed_time * 2
        )

        move_penalty = self.moves * 3

        self.score = max(
            0,
            int(
                score_bonus
                + battery_bonus
                - time_penalty
                - move_penalty
            ),
        )

    def calculate_final_score(self):
        """Calculate score after reaching the exit."""

        multiplier = (
            self.get_difficulty_multiplier()
        )

        completion_bonus = float(
            self.get_setting(
                "score_bonus",
                1500 * multiplier,
            )
        )

        battery_bonus = (
            self.battery_percentage
            * 10
            * multiplier
        )

        speed_bonus = max(
            0,
            1000
            - self.elapsed_time * 5,
        )

        efficiency_bonus = max(
            0,
            800 - self.moves * 4,
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

    # =========================================================
    # EXIT AND WIN
    # =========================================================

    def update_exit_particles(
        self,
        delta_time,
    ):
        """Create particles around the exit."""
        if self.maze is None:
            return

        self.exit_particle_timer -= delta_time

        if self.exit_particle_timer > 0:
            return

        self.exit_particle_timer = self.exit_particle_interval

        exit_row, exit_col = self.get_exit_position()
        exit_x, exit_y = self.get_cell_center(exit_row, exit_col)

        self.particle_manager.create_exit_particle(
            exit_x,
            exit_y,
            radius=max(10, self.maze.cell_size // 2),
        )

    def check_win_condition(self):
        """Check whether the player reached the exit."""

        if (
            self.game_state
            != GAME_STATE_PLAYING
        ):
            return

        if (
            self.player is None
            or self.maze is None
        ):
            return

        player_position = (
            self.player.row,
            self.player.col,
        )

        if (
            player_position
            == self.get_exit_position()
        ):
            self.complete_game()

    def complete_game(self):
        """Finish the current maze."""

        if self.win_animation_started:
            return

        self.win_animation_started = True

        self.update_elapsed_time()

        self.final_score = (
            self.calculate_final_score()
        )

        exit_row, exit_col = (
            self.get_exit_position()
        )

        exit_x, exit_y = (
            self.get_cell_center(
                exit_row,
                exit_col,
            )
        )

        if hasattr(
            self.particle_manager,
            "create_win_burst",
        ):
            self.particle_manager.create_win_burst(
                exit_x,
                exit_y,
            )

        self.open_result_screen()
        self.game_state = GAME_STATE_WON

    def open_result_screen(self):
        """Open the result screen with correct arguments."""
        if self.result_screen is not None:
            self.result_screen.open(
                self.selected_difficulty,
                self.moves,
                int(self.elapsed_time),
                self.battery_percentage,
                self.final_score,
            )

    # =========================================================
    # DRAWING
    # =========================================================

    def draw(self):
        """Draw the active screen."""

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
            self.pause_screen.draw(self.screen)

        elif self.game_state == GAME_STATE_WON:
            self.draw_result()

        if hasattr(
            self.transition_manager,
            "draw",
        ):
            self.transition_manager.draw(
                self.screen
            )

        pygame.display.flip()

    def draw_menu(self):
        """Draw the main menu."""

        self.main_menu.draw(self.screen)

    def draw_gameplay(self):
        """Draw the maze and all gameplay objects."""

        if (
            self.maze is None
            or self.player is None
        ):
            return

        self.screen.fill(BACKGROUND)

        visibility_radius = (
            self.get_visibility_radius()
        )

        self.draw_maze(visibility_radius)
        self.draw_exit(visibility_radius)
        self.draw_batteries(
            visibility_radius
        )
        self.draw_particles()
        self.draw_player_torch(
            visibility_radius
        )
        self.draw_player(visibility_radius)
        self.draw_hud()

    def draw_maze(self, visibility_radius):
        """Draw Maze using its actual parameters."""
        self.maze.draw(
            self.screen,
            self.player.row,
            self.player.col,
            visibility_radius,
        )

    def draw_batteries(
        self,
        visibility_radius,
    ):
        """Draw battery pickups."""
        if self.battery_manager is not None:
            self.battery_manager.draw(
                self.screen,
                self.player.row,
                self.player.col,
                visibility_radius,
            )

    def draw_particles(self):
        """Draw all particles."""

        if hasattr(
            self.particle_manager,
            "draw_particles",
        ):
            self.particle_manager.draw_particles(
                self.screen
            )

        elif hasattr(
            self.particle_manager,
            "draw",
        ):
            self.particle_manager.draw(
                self.screen
            )

    def draw_player_torch(
        self,
        visibility_radius,
    ):
        """
        Draw the torch glow.
        """
        if not hasattr(self.player, "draw_torch_glow"):
            return

        glow_radius = int(
            self.maze.cell_size
            * (
                visibility_radius
                + 0.75
            )
        )

        glow_radius = max(
            self.maze.cell_size,
            glow_radius,
        )

        self.player.draw_torch_glow(
            self.screen,
            glow_radius,
            self.battery_percentage,
        )

    def draw_player(self, visibility_radius):
        """Draw the player."""
        self.player.draw(
            self.screen,
            visibility_radius,
            self.battery_percentage,
        )

    def draw_hud(self):
        """Draw current gameplay statistics."""
        if self.hud is not None:
            self.hud.draw(
                self.screen,
                self.selected_difficulty,
                self.moves,
                int(self.elapsed_time),
                self.battery_percentage,
                self.score,
                self.get_remaining_battery_count(),
            )

    def draw_exit(
        self,
        visibility_radius,
    ):
        """Draw the animated exit portal."""

        exit_row, exit_col = (
            self.get_exit_position()
        )

        if not self.is_cell_visible(
            exit_row,
            exit_col,
            visibility_radius,
        ):
            return

        center_x, center_y = (
            self.get_cell_center(
                exit_row,
                exit_col,
            )
        )

        pulse = (
            math.sin(
                pygame.time.get_ticks()
                * 0.006
            )
            + 1
        ) / 2

        outer_radius = max(
            5,
            int(
                self.maze.cell_size
                * (
                    0.35
                    + pulse * 0.08
                )
            ),
        )

        inner_radius = max(
            3,
            int(outer_radius * 0.55),
        )

        glow_surface = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
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
            (center_x, center_y),
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
            (center_x, center_y),
            outer_radius + 7,
        )

        self.screen.blit(
            glow_surface,
            (0, 0),
        )

        pygame.draw.circle(
            self.screen,
            EXIT_COLOR,
            (center_x, center_y),
            outer_radius,
            width=max(
                2,
                self.maze.cell_size // 10,
            ),
        )

        pygame.draw.circle(
            self.screen,
            GREEN_LIGHT,
            (center_x, center_y),
            inner_radius,
        )

    def is_cell_visible(
        self,
        row,
        col,
        visibility_radius,
    ):
        """Check whether a cell is visible."""
        if self.maze is None or self.player is None:
            return False
        return self.maze.is_cell_visible(
            row,
            col,
            self.player.row,
            self.player.col,
            visibility_radius,
        )

    def draw_result(self):
        """Draw the victory screen."""

        self.result_screen.draw(self.screen)

    # =========================================================
    # MAIN LOOP
    # =========================================================

    def run(self):
        """Run the Pygame loop."""

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

    @staticmethod
    def close():
        """Close the game."""

        pygame.quit()
        sys.exit()