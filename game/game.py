import math
import random
import sys
import time

import pygame

from game.battery import BatteryManager
from game.enemy import ShadowMonster
from game.maze import Maze
from game.particles import ParticleManager
from game.player import Player
from game.powerups import PowerUpManager
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
    """
    Main controller of the Invisible Maze game.
    """

    def __init__(self):
        pygame.init()

        pygame.display.set_caption(
            "Invisible Maze"
        )

        self.screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        )

        self.clock = pygame.time.Clock()
        self.running = True

        self.fonts = create_fonts()

        # =================================================
        # GAME STATE
        # =================================================

        self.game_state = GAME_STATE_MENU
        self.previous_game_state = (
            GAME_STATE_MENU
        )

        self.selected_difficulty = "Easy"
        self.difficulty_config = None

        # =================================================
        # GAME OBJECTS
        # =================================================

        self.maze = None
        self.player = None
        self.battery_manager = None
        self.shadow_monster = None
        self.powerup_manager = None

        # =================================================
        # SHARED SYSTEMS
        # =================================================

        self.particle_manager = ParticleManager(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        self.hud = HUD(
            self.fonts
        )

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

        # =================================================
        # GAME VALUES
        # =================================================

        self.maximum_battery = 100.0
        self.battery_percentage = 100.0

        self.moves = 0
        self.score = 0
        self.final_score = 0
        self.screen_flash = 0.0
        self.powerup_score_bonus = 0

        self.elapsed_time = 0.0
        self.game_start_time = 0.0

        self.pause_start_time = 0.0
        self.total_paused_time = 0.0

        self.exit_particle_timer = 0.0
        self.exit_particle_interval = 0.08

        self.win_animation_started = False

        self.movement_cooldown = 0.0
        self.movement_delay = 0.08

        self.zero_battery_message_shown = (
            False
        )

        # =================================================
        # MONSTER VALUES
        # =================================================

        self.monster_damage_cooldown = 0.0
        self.monster_damage_delay = 2.0

        self.monster_warning_shown = False
        self.monster_hit_flash = 0.0

    # =====================================================
    # SETTINGS HELPERS
    # =====================================================

    def get_setting(
        self,
        key,
        default_value,
    ):
        if self.difficulty_config is None:
            return default_value

        return self.difficulty_config.get(
            key,
            default_value,
        )

    def get_start_position(self):
        if hasattr(
            self.maze,
            "start_position",
        ):
            position = (
                self.maze.start_position
            )

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

        return 1, 1

    def get_exit_position(self):
        if hasattr(
            self.maze,
            "exit_position",
        ):
            position = (
                self.maze.exit_position
            )

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

        return (
            self.maze.rows - 2,
            self.maze.cols - 2,
        )

    def maze_is_path(
        self,
        row,
        col,
    ):
        if self.maze is None:
            return False

        if hasattr(
            self.maze,
            "is_path",
        ):
            try:
                return bool(
                    self.maze.is_path(
                        row,
                        col,
                    )
                )

            except (
                TypeError,
                IndexError,
            ):
                return False

        if hasattr(
            self.maze,
            "grid",
        ):
            if row < 0 or col < 0:
                return False

            if row >= len(self.maze.grid):
                return False

            if col >= len(
                self.maze.grid[row]
            ):
                return False

            return (
                self.maze.grid[row][col]
                != 1
            )

        return False

    # =====================================================
    # START AND RESTART
    # =====================================================

    def start_game(
        self,
        difficulty,
    ):
        if difficulty not in DIFFICULTY_SETTINGS:
            difficulty = "Easy"

        self.selected_difficulty = difficulty

        self.difficulty_config = (
            DIFFICULTY_SETTINGS[difficulty]
        )

        rows = int(
            self.get_setting(
                "rows",
                17,
            )
        )

        cols = int(
            self.get_setting(
                "cols",
                rows,
            )
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

        monster_move_interval = float(
            self.get_setting(
                "monster_move_interval",
                {
                    "Easy": 1.20,
                    "Medium": 0.85,
                    "Hard": 0.60,
                }.get(
                    difficulty,
                    1.0,
                ),
            )
        )

        monster_damage = float(
            self.get_setting(
                "monster_damage",
                {
                    "Easy": 10,
                    "Medium": 15,
                    "Hard": 20,
                }.get(
                    difficulty,
                    15,
                ),
            )
        )

        # =================================================
        # CALCULATE MAZE SIZE
        # =================================================

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

        cell_size = max(
            8,
            cell_size,
        )

        maze_pixel_width = (
            cols * cell_size
        )

        maze_pixel_height = (
            rows * cell_size
        )

        maze_start_x = (
            SCREEN_WIDTH
            - maze_pixel_width
        ) // 2

        maze_start_y = (
            MAZE_TOP_MARGIN
            + (
                available_height
                - maze_pixel_height
            ) // 2
        )

        # =================================================
        # CREATE MAZE
        # =================================================

        self.maze = Maze(
            rows=rows,
            cols=cols,
            cell_size=cell_size,
            start_x=maze_start_x,
            start_y=maze_start_y,
        )

        start_row, start_col = (
            self.get_start_position()
        )

        # =================================================
        # CREATE PLAYER
        # =================================================

        self.player = Player(
            self.maze,
            start_row,
            start_col,
        )

        # =================================================
        # CREATE POWER-UP MANAGER
        # =================================================
        from game.powerups import PowerUpManager
        self.powerup_manager = PowerUpManager(self.maze, self.fonts)
        import game.player
        self.powerup_manager.original_player_speed = float(game.player.PLAYER_MOVE_SPEED)
        self.powerup_manager.spawn_powerups(self, int(self.get_setting("powerup_count", 3)))

        # =================================================
        # CREATE MONSTER
        # =================================================

        monster_row, monster_col = (
            self.find_monster_start_position(
                start_row,
                start_col,
            )
        )

        self.shadow_monster = (
            ShadowMonster(
                maze=self.maze,
                start_row=monster_row,
                start_col=monster_col,
                move_interval=(
                    monster_move_interval
                ),
                damage=monster_damage,
            )
        )

        # =================================================
        # CREATE BATTERY MANAGER
        # =================================================

        try:
            self.battery_manager = (
                BatteryManager(
                    maze=self.maze,
                    pickup_count=battery_count,
                    restore_amount=(
                        battery_restore
                    ),
                )
            )

        except TypeError:
            try:
                self.battery_manager = (
                    BatteryManager(
                        self.maze,
                        battery_count,
                        battery_restore,
                    )
                )

            except TypeError:
                self.battery_manager = (
                    BatteryManager(
                        maze=self.maze,
                        battery_count=(
                            battery_count
                        ),
                        battery_restore=(
                            battery_restore
                        ),
                    )
                )

        # =================================================
        # RESET VALUES
        # =================================================

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
        self.screen_flash = 0.0
        self.powerup_score_bonus = 0

        self.elapsed_time = 0.0
        self.game_start_time = time.time()

        self.pause_start_time = 0.0
        self.total_paused_time = 0.0

        self.exit_particle_timer = 0.0

        self.win_animation_started = False

        self.zero_battery_message_shown = (
            False
        )

        self.movement_cooldown = 0.0

        self.monster_damage_cooldown = 0.0
        self.monster_warning_shown = False
        self.monster_hit_flash = 0.0

        if hasattr(
            self.particle_manager,
            "clear",
        ):
            self.particle_manager.clear()

        if hasattr(
            self.hud,
            "displayed_battery",
        ):
            displayed_battery = (
                self.hud.displayed_battery
            )

            if hasattr(
                displayed_battery,
                "snap",
            ):
                displayed_battery.snap(
                    self.battery_percentage
                )

        if hasattr(
            self.hud,
            "displayed_score",
        ):
            displayed_score = (
                self.hud.displayed_score
            )

            if hasattr(
                displayed_score,
                "snap",
            ):
                displayed_score.snap(0)

        self.game_state = GAME_STATE_PLAYING

        if hasattr(
            self.hud,
            "show_notification",
        ):
            self.hud.show_notification(
                f"{difficulty} maze started"
            )

    def find_monster_start_position(
        self,
        player_row,
        player_col,
    ):
        exit_row, exit_col = (
            self.get_exit_position()
        )

        possible_positions = []

        for row in range(
            1,
            self.maze.rows - 1,
        ):
            for col in range(
                1,
                self.maze.cols - 1,
            ):
                if not self.maze_is_path(
                    row,
                    col,
                ):
                    continue

                if (
                    row == player_row
                    and col == player_col
                ):
                    continue

                distance_from_player = (
                    abs(row - player_row)
                    + abs(col - player_col)
                )

                distance_from_exit = (
                    abs(row - exit_row)
                    + abs(col - exit_col)
                )

                if (
                    distance_from_player >= 8
                    and distance_from_exit >= 3
                ):
                    possible_positions.append(
                        (
                            distance_from_player,
                            row,
                            col,
                        )
                    )

        if possible_positions:
            maximum_distance = max(
                item[0]
                for item in possible_positions
            )

            far_positions = [
                item
                for item in possible_positions
                if item[0]
                >= maximum_distance - 4
            ]

            _, row, col = random.choice(
                far_positions
            )

            return row, col

        if self.maze_is_path(
            exit_row,
            exit_col,
        ):
            return exit_row, exit_col

        return player_row, player_col

    def restart_game(self):
        self.start_game(
            self.selected_difficulty
        )

    def open_main_menu(self):
        self.game_state = GAME_STATE_MENU

        if self.powerup_manager:
            self.powerup_manager.reset_effects(self)

        self.maze = None
        self.player = None
        self.battery_manager = None
        self.shadow_monster = None
        self.powerup_manager = None

        if hasattr(
            self.particle_manager,
            "clear",
        ):
            self.particle_manager.clear()

    # =====================================================
    # EVENT HANDLING
    # =====================================================

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if (
                hasattr(
                    self.transition_manager,
                    "is_active",
                )
                and self.transition_manager.is_active()
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

            elif (
                self.game_state
                == GAME_STATE_WON
            ):
                self.handle_result_event(event)

    def handle_menu_event(
        self,
        event,
    ):
        action = self.main_menu.handle_event(
            event
        )

        if action is None:
            return

        if isinstance(
            action,
            tuple,
        ):
            action_name = action[0]

            action_value = (
                action[1]
                if len(action) > 1
                else None
            )

        else:
            action_name = action
            action_value = None

        if action_name == "start":
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

        elif action_name in (
            "easy",
            "Easy",
        ):
            self.start_transition(
                callback=lambda:
                self.start_game("Easy"),
                transition_type="circle",
            )

        elif action_name in (
            "medium",
            "Medium",
        ):
            self.start_transition(
                callback=lambda:
                self.start_game("Medium"),
                transition_type="circle",
            )

        elif action_name in (
            "hard",
            "Hard",
        ):
            self.start_transition(
                callback=lambda:
                self.start_game("Hard"),
                transition_type="circle",
            )

        elif action_name == "settings":
            if hasattr(
                self.hud,
                "show_notification",
            ):
                self.hud.show_notification(
                    "Settings screen will be added later"
                )

        elif action_name in (
            "quit",
            "exit",
        ):
            self.running = False

    def handle_playing_event(
        self,
        event,
    ):
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (
            pygame.K_p,
            pygame.K_ESCAPE,
        ):
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
            self.try_move_player(
                direction
            )

    def handle_pause_event(
        self,
        event,
    ):
        if (
            event.type == pygame.KEYDOWN
            and event.key
            in (
                pygame.K_p,
                pygame.K_ESCAPE,
            )
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

    def handle_result_event(
        self,
        event,
    ):
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

    def start_transition(
        self,
        callback,
        transition_type="fade",
    ):
        if transition_type == "circle":
            if hasattr(
                self.transition_manager,
                "start_circle",
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

        else:
            callback()

    def get_direction_from_key(
        self,
        key,
    ):
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

    # =====================================================
    # PLAYER MOVEMENT
    # =====================================================

    def try_move_player(
        self,
        direction,
    ):
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

        moved = self.player.try_move(
            row_change,
            col_change,
        )

        if moved:
            self.moves += 1

            self.movement_cooldown = (
                self.movement_delay
            )

            self.check_battery_collection()
            self.check_win_condition()

        else:
            player_x, player_y = (
                self.get_player_center()
            )

            if hasattr(
                self.particle_manager,
                "create_wall_hit_sparks",
            ):
                try:
                    self.particle_manager.create_wall_hit_sparks(
                        player_x,
                        player_y,
                        direction,
                    )

                except TypeError:
                    self.particle_manager.create_wall_hit_sparks(
                        player_x,
                        player_y,
                    )

    def get_player_center(self):
        if self.player is None:
            return 0, 0

        if hasattr(
            self.player,
            "get_center",
        ):
            return self.player.get_center()

        if (
            hasattr(self.player, "x")
            and hasattr(self.player, "y")
        ):
            return (
                int(self.player.x),
                int(self.player.y),
            )

        return self.maze.get_cell_center(
            self.player.row,
            self.player.col,
        )

    # =====================================================
    # BATTERY PICKUPS
    # =====================================================

    def check_battery_collection(self):
        if self.battery_manager is None:
            return

        restored_amount = 0

        if hasattr(
            self.battery_manager,
            "collect_at",
        ):
            restored_amount = (
                self.battery_manager.collect_at(
                    self.player.row,
                    self.player.col,
                )
            )

        elif hasattr(
            self.battery_manager,
            "collect",
        ):
            restored_amount = (
                self.battery_manager.collect(
                    self.player.row,
                    self.player.col,
                )
            )

        if restored_amount is None:
            restored_amount = 0

        if isinstance(
            restored_amount,
            bool,
        ):
            if restored_amount:
                restored_amount = (
                    self.get_setting(
                        "battery_restore",
                        25,
                    )
                )

            else:
                restored_amount = 0

        try:
            restored_amount = float(
                restored_amount
            )

        except (
            TypeError,
            ValueError,
        ):
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
            self.maze.get_cell_center(
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

        if hasattr(
            self.hud,
            "show_notification",
        ):
            self.hud.show_notification(
                f"Battery collected: +{actual_restored}%"
            )

    # =====================================================
    # PAUSE SYSTEM
    # =====================================================

    def pause_game(self):
        if (
            self.game_state
            != GAME_STATE_PLAYING
        ):
            return

        self.game_state = GAME_STATE_PAUSED
        self.pause_start_time = time.time()

        if hasattr(
            self.pause_screen,
            "open",
        ):
            self.pause_screen.open()

    def resume_game(self):
        if (
            self.game_state
            != GAME_STATE_PAUSED
        ):
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

    def update(
        self,
        delta_time,
    ):
        if hasattr(
            self.transition_manager,
            "update",
        ):
            self.transition_manager.update(
                delta_time
            )

        if hasattr(
            self.particle_manager,
            "update",
        ):
            try:
                self.particle_manager.update(
                    delta_time,
                    update_fireflies=True,
                )

            except TypeError:
                self.particle_manager.update(
                    delta_time
                )

        if self.game_state == GAME_STATE_MENU:
            self.update_menu(
                delta_time
            )

        elif (
            self.game_state
            == GAME_STATE_PLAYING
        ):
            self.update_playing(
                delta_time
            )

        elif (
            self.game_state
            == GAME_STATE_PAUSED
        ):
            self.update_paused(
                delta_time
            )

        elif (
            self.game_state
            == GAME_STATE_WON
        ):
            self.update_won(
                delta_time
            )

    def update_menu(
        self,
        delta_time,
    ):
        if hasattr(
            self.main_menu,
            "update",
        ):
            self.main_menu.update(
                delta_time
            )

    def update_playing(
        self,
        delta_time,
    ):
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

        self.screen_flash = max(0.0, self.screen_flash - delta_time)

        if self.powerup_manager:
            self.powerup_manager.update(delta_time, self)
            self.powerup_manager.check_collisions(self)

        if hasattr(
            self.player,
            "update",
        ):
            self.player.update(
                delta_time
            )

        self.update_shadow_monster(
            delta_time
        )

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

        player_x, player_y = (
            self.get_player_center()
        )

        if getattr(
            self.player,
            "is_moving",
            False,
        ):
            if hasattr(
                self.particle_manager,
                "create_player_trail",
            ):
                self.particle_manager.create_player_trail(
                    player_x,
                    player_y,
                )

        if hasattr(
            self.hud,
            "update",
        ):
            try:
                self.hud.update(
                    delta_time=delta_time,
                    battery=(
                        self.battery_percentage
                    ),
                    score=self.score,
                )

            except TypeError:
                self.hud.update(
                    delta_time,
                    self.battery_percentage,
                    self.score,
                )

        if (
            self.battery_percentage <= 0
            and not
            self.zero_battery_message_shown
        ):
            self.battery_percentage = 0

            self.zero_battery_message_shown = (
                True
            )

            if hasattr(
                self.hud,
                "show_notification",
            ):
                self.hud.show_notification(
                    "Your torch has completely faded"
                )

        if self.battery_percentage > 0:
            self.zero_battery_message_shown = (
                False
            )

        self.check_win_condition()

    def update_shadow_monster(
        self,
        delta_time,
    ):
        if (
            self.shadow_monster is None
            or self.player is None
        ):
            return

        if self.powerup_manager and self.powerup_manager.is_active("Freeze"):
            return

        self.monster_damage_cooldown = max(
            0.0,
            self.monster_damage_cooldown
            - delta_time,
        )

        self.monster_hit_flash = max(
            0.0,
            self.monster_hit_flash
            - delta_time,
        )

        self.shadow_monster.update(
            delta_time=delta_time,
            player_row=self.player.row,
            player_col=self.player.col,
            battery_percentage=(
                self.battery_percentage
            ),
        )

        distance = (
            self.shadow_monster
            .distance_to_player(
                self.player.row,
                self.player.col,
            )
        )

        if (
            distance <= 4
            and not self.monster_warning_shown
        ):
            self.monster_warning_shown = True

            if hasattr(
                self.hud,
                "show_notification",
            ):
                self.hud.show_notification(
                    "Something is following you..."
                )

        elif distance > 4:
            self.monster_warning_shown = False

        if (
            self.shadow_monster
            .is_touching_player(
                self.player.row,
                self.player.col,
            )
            and self.monster_damage_cooldown
            <= 0
        ):
            self.damage_player_from_monster()

    def damage_player_from_monster(self):
        if self.shadow_monster is None:
            return

        damage = float(
            self.shadow_monster.damage
        )

        self.battery_percentage = max(
            0.0,
            self.battery_percentage
            - damage,
        )

        self.monster_damage_cooldown = (
            self.monster_damage_delay
        )

        self.monster_hit_flash = 0.35

        player_x, player_y = (
            self.get_player_center()
        )

        if hasattr(
            self.particle_manager,
            "create_wall_hit_sparks",
        ):
            try:
                self.particle_manager.create_wall_hit_sparks(
                    player_x,
                    player_y,
                    (0, 0),
                )

            except TypeError:
                try:
                    self.particle_manager.create_wall_hit_sparks(
                        player_x,
                        player_y,
                    )

                except TypeError:
                    pass

        if hasattr(
            self.hud,
            "show_notification",
        ):
            self.hud.show_notification(
                f"Shadow attack! -{int(damage)}% battery"
            )

    def update_paused(
        self,
        delta_time,
    ):
        if hasattr(
            self.pause_screen,
            "update",
        ):
            self.pause_screen.update(
                delta_time
            )

    def update_won(
        self,
        delta_time,
    ):
        if hasattr(
            self.result_screen,
            "update",
        ):
            self.result_screen.update(
                delta_time
            )

    # =====================================================
    # TIMER AND BATTERY
    # =====================================================

    def update_elapsed_time(self):
        if self.game_start_time <= 0:
            self.elapsed_time = 0
            return

        self.elapsed_time = (
            time.time()
            - self.game_start_time
            - self.total_paused_time
        )

        self.elapsed_time = max(
            0,
            self.elapsed_time,
        )

    def update_battery(
        self,
        delta_time,
    ):
        drain_rate = float(
            self.get_setting(
                "battery_drain",
                1.0,
            )
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
        base_radius = int(
            self.get_setting(
                "visibility_radius",
                self.get_setting(
                    "maximum_visibility",
                    4,
                ),
            )
        )

        minimum_radius = int(
            self.get_setting(
                "minimum_visibility",
                1,
            )
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

        radius = max(
            minimum_radius,
            dynamic_radius,
        )

        if self.powerup_manager and self.powerup_manager.is_active("Torch"):
            radius += 3

        return radius

    # =====================================================
    # SCORE
    # =====================================================

    def get_difficulty_multiplier(self):
        multipliers = {
            "Easy": 1.0,
            "Medium": 1.5,
            "Hard": 2.0,
        }

        return multipliers.get(
            self.selected_difficulty,
            1.0,
        )

    def update_score(self):
        multiplier = (
            self.get_difficulty_multiplier()
        )

        score_bonus = self.get_setting(
            "score_bonus",
            int(1000 * multiplier),
        )

        battery_bonus = (
            self.battery_percentage
            * 5
            * multiplier
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
                score_bonus
                + battery_bonus
                - time_penalty
                - move_penalty
                + getattr(self, "powerup_score_bonus", 0)
            ),
        )

    def calculate_final_score(self):
        multiplier = (
            self.get_difficulty_multiplier()
        )

        completion_bonus = self.get_setting(
            "score_bonus",
            int(1500 * multiplier),
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

    # =====================================================
    # EXIT AND WIN
    # =====================================================

    def update_exit_particles(
        self,
        delta_time,
    ):
        if self.maze is None:
            return

        self.exit_particle_timer -= (
            delta_time
        )

        if self.exit_particle_timer > 0:
            return

        self.exit_particle_timer = (
            self.exit_particle_interval
        )

        exit_row, exit_col = (
            self.get_exit_position()
        )

        exit_x, exit_y = (
            self.maze.get_cell_center(
                exit_row,
                exit_col,
            )
        )

        if hasattr(
            self.particle_manager,
            "create_exit_particle",
        ):
            try:
                self.particle_manager.create_exit_particle(
                    exit_x,
                    exit_y,
                    radius=max(
                        10,
                        self.maze.cell_size // 2,
                    ),
                )

            except TypeError:
                self.particle_manager.create_exit_particle(
                    exit_x,
                    exit_y,
                )

    def check_win_condition(self):
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
            != self.get_exit_position()
        ):
            return

        self.complete_game()

    def complete_game(self):
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
            self.maze.get_cell_center(
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

        if hasattr(
            self.result_screen,
            "open",
        ):
            try:
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

            except TypeError:
                self.result_screen.open(
                    self.selected_difficulty,
                    self.moves,
                    int(self.elapsed_time),
                    self.battery_percentage,
                    self.final_score,
                )

        self.game_state = GAME_STATE_WON

    # =====================================================
    # BATTERY INFORMATION
    # =====================================================

    def get_remaining_battery_count(self):
        if self.battery_manager is None:
            return 0

        if hasattr(
            self.battery_manager,
            "get_remaining_count",
        ):
            return (
                self.battery_manager
                .get_remaining_count()
            )

        if hasattr(
            self.battery_manager,
            "batteries",
        ):
            return len(
                self.battery_manager.batteries
            )

        if hasattr(
            self.battery_manager,
            "pickups",
        ):
            return len(
                self.battery_manager.pickups
            )

        return 0

    # =====================================================
    # DRAW
    # =====================================================

    def draw(self):
        self.screen.fill(
            BACKGROUND
        )

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

        elif (
            self.game_state
            == GAME_STATE_WON
        ):
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
        self.main_menu.draw(
            self.screen
        )

    def draw_gameplay(self):
        if (
            self.maze is None
            or self.player is None
        ):
            return

        self.screen.fill(
            BACKGROUND
        )

        visibility_radius = (
            self.get_visibility_radius()
        )

        self.draw_maze(
            visibility_radius
        )

        self.draw_exit(
            visibility_radius
        )

        self.draw_batteries(
            visibility_radius
        )

        if self.powerup_manager:
            self.powerup_manager.draw(self.screen)

        self.draw_shadow_monster(
            visibility_radius
        )

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

        if hasattr(
            self.player,
            "draw_torch_glow",
        ):
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

            battery_pct = self.battery_percentage
            if self.powerup_manager and self.powerup_manager.is_active("Torch"):
                battery_pct = max(100.0, battery_pct + 50.0)

            self.player.draw_torch_glow(
                self.screen,
                glow_radius,
                battery_pct,
            )

        if self.powerup_manager and self.powerup_manager.is_active("Ghost"):
            player_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            self.player.draw(
                player_surface,
                visibility_radius,
                self.battery_percentage,
            )
            player_surface.set_alpha(140)
            self.screen.blit(player_surface, (0, 0))
        else:
            self.player.draw(
                self.screen,
                visibility_radius,
                self.battery_percentage,
            )

        self.draw_screen_flash()
        self.draw_monster_damage_flash()
        self.draw_hud()

    def draw_shadow_monster(
        self,
        visibility_radius,
    ):
        if self.shadow_monster is None:
            return

        self.shadow_monster.draw(
            surface=self.screen,
            player_row=self.player.row,
            player_col=self.player.col,
            visibility_radius=(
                visibility_radius
            ),
        )

    def draw_screen_flash(self):
        if getattr(self, "screen_flash", 0.0) <= 0:
            return

        maximum_flash_time = 0.20
        flash_ratio = self.screen_flash / maximum_flash_time
        alpha = int(110 * flash_ratio)

        flash_surface = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        flash_surface.fill(
            (
                255,
                215,
                0,
                alpha,
            )
        )

        self.screen.blit(
            flash_surface,
            (0, 0),
        )

    def draw_monster_damage_flash(self):
        if self.monster_hit_flash <= 0:
            return

        maximum_flash_time = 0.35

        flash_ratio = (
            self.monster_hit_flash
            / maximum_flash_time
        )

        alpha = int(
            105 * flash_ratio
        )

        flash_surface = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        flash_surface.fill(
            (
                170,
                0,
                15,
                alpha,
            )
        )

        self.screen.blit(
            flash_surface,
            (0, 0),
        )

    def draw_maze(
        self,
        visibility_radius,
    ):
        try:
            self.maze.draw(
                surface=self.screen,
                player_row=self.player.row,
                player_col=self.player.col,
                visibility_radius=(
                    visibility_radius
                ),
            )

        except TypeError:
            try:
                self.maze.draw(
                    self.screen,
                    self.player.row,
                    self.player.col,
                    visibility_radius,
                )

            except TypeError:
                self.maze.draw(
                    self.screen
                )

    def draw_batteries(
        self,
        visibility_radius,
    ):
        if self.battery_manager is None:
            return

        if not hasattr(
            self.battery_manager,
            "draw",
        ):
            return

        try:
            self.battery_manager.draw(
                surface=self.screen,
                player_row=self.player.row,
                player_col=self.player.col,
                visibility_radius=(
                    visibility_radius
                ),
            )

        except TypeError:
            try:
                self.battery_manager.draw(
                    self.screen,
                    self.player.row,
                    self.player.col,
                    visibility_radius,
                )

            except TypeError:
                self.battery_manager.draw(
                    self.screen
                )

    def draw_hud(self):
        remaining_batteries = (
            self.get_remaining_battery_count()
        )

        try:
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
                active_powerups=(
                    self.powerup_manager.active_powerups
                    if self.powerup_manager
                    else None
                ),
            )

        except TypeError:
            try:
                self.hud.draw(
                    self.screen,
                    self.selected_difficulty,
                    self.moves,
                    int(self.elapsed_time),
                    self.battery_percentage,
                    self.score,
                    remaining_batteries,
                )

            except TypeError:
                self.hud.draw(
                    self.screen
                )

    def draw_exit(
        self,
        visibility_radius,
    ):
        exit_row, exit_col = (
            self.get_exit_position()
        )

        is_visible = self.is_cell_visible(
            exit_row,
            exit_col,
            visibility_radius,
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
                outer_radius
                * 0.55
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

    def is_cell_visible(
        self,
        row,
        col,
        visibility_radius,
    ):
        if hasattr(
            self.maze,
            "is_cell_visible",
        ):
            try:
                return self.maze.is_cell_visible(
                    row,
                    col,
                    self.player.row,
                    self.player.col,
                    visibility_radius,
                )

            except TypeError:
                pass

        distance = (
            abs(row - self.player.row)
            + abs(col - self.player.col)
        )

        return (
            distance
            <= visibility_radius
        )

    def draw_result(self):
        self.result_screen.draw(
            self.screen
        )

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def run(self):
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
        pygame.quit()
        sys.exit()