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
from game.traps import TrapManager
from game.doors import DoorManager
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

from game.save_manager import SaveManager
from game.levels import LevelManager
from game.themes import ThemeManager
from ui.theme_select import WorldSelectScreen
from ui.level_select import LevelSelectScreen
from ui.customization_screen import CustomizationScreen

GAME_STATE_WORLD_SELECT = 4
GAME_STATE_LEVEL_SELECT = 5
GAME_STATE_CUSTOMIZATION = 6


class TorchRenderer:
    """
    Renders a smooth, cached darkness mask overlay with a soft circular torch cutout centered at (px, py).
    Maintains 60 FPS performance via cached radial gradient surfaces.
    """

    def __init__(self):
        self.cached_masks = {}

    def get_torch_surface(self, radius):
        r_key = int(max(10, radius))
        if r_key in self.cached_masks:
            return self.cached_masks[r_key]

        surf = pygame.Surface((r_key * 2, r_key * 2), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 255))

        steps = 35
        for i in range(steps, -1, -1):
            t = i / steps
            r = int(r_key * t)
            alpha = int(255 * (t ** 1.8))
            pygame.draw.circle(surf, (0, 0, 0, alpha), (r_key, r_key), r)

        self.cached_masks[r_key] = surf
        return surf

    def apply(self, surface, px, py, radius, theme_name="Ninja World"):
        r_int = int(max(15, radius))
        torch_surf = self.get_torch_surface(r_int)

        darkness = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        darkness.fill((0, 0, 0, 255))

        darkness.blit(
            torch_surf,
            (int(px - r_int), int(py - r_int)),
            special_flags=pygame.BLEND_RGBA_MIN,
        )

        surface.blit(darkness, (0, 0))

        # Add warm theme-specific ambient light glow inside torch
        glow_colors = {
            "Ninja World": (255, 160, 60, 22),
            "Spring World": (180, 255, 200, 18),
            "Frozen World": (160, 220, 255, 22),
            "Haunted World": (180, 140, 255, 20),
            "Cyber World": (0, 245, 255, 18),
            "Desert Temple World": (255, 215, 90, 22),
        }
        accent = glow_colors.get(theme_name, (255, 215, 90, 20))
        glow_surf = pygame.Surface((r_int * 2, r_int * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, accent, (r_int, r_int), int(r_int * 0.6))
        pygame.draw.circle(
            glow_surf,
            (accent[0], accent[1], accent[2], accent[3] // 2),
            (r_int, r_int),
            int(r_int * 0.85),
        )
        surface.blit(glow_surf, (int(px - r_int), int(py - r_int)))


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
        self.trap_manager = None
        self.door_manager = None

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

        self.torch_renderer = TorchRenderer()

        # =================================================
        # SAVE PROGRESS AND WORLD THEME
        # =================================================

        self.save_data = SaveManager.load()
        self.selected_world_id = "1"
        self.selected_level_id = "1-1"

        self.main_menu.save_data = self.save_data
        self.main_menu.selected_world_id = self.selected_world_id

        self.selected_theme_name = self.save_data.get("selected_theme", "Ninja World")
        ThemeManager.apply_theme(self.selected_theme_name)
        self.hud.theme_name = self.selected_theme_name

        self.world_select_screen = None
        self.level_select_screen = None
        self.customization_screen = None

        # Special world mechanic variables
        self.cyber_glitch_timer = 0.0
        self.cyber_glitch_active = False
        self.desert_sandstorm_timer = 0.0
        self.desert_sandstorm_active = False
        self.slippery_ice_tiles = set()
        self.haunted_wall_tiles = set()
        self.haunted_wall_timer = 0.0
        self.lantern_positions = []
        self.spring_flower_positions = []

        # =================================================
        # GAME VALUES
        # =================================================
        # =================================================

        self.maximum_battery = 100.0
        self.battery_percentage = 100.0

        self.moves = 0
        self.score = 0
        self.final_score = 0
        self.screen_flash = 0.0
        self.powerup_score_bonus = 0
        self.slow_trap_timer = 0.0
        self.darkness_trap_timer = 0.0
        self.alarm_trap_timer = 0.0
        self.battery_leak_timer = 0.0
        self.teleport_flash = 0.0
        self.trap_immunity_timer = 0.0

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
        level_id = getattr(self, "selected_level_id", None)
        if level_id:
            from game.levels import LevelManager
            config = LevelManager.get_level(level_id)
            if config and hasattr(config, key):
                return getattr(config, key)

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

    def get_reachable_positions(self, start_row, start_col):
        """
        Calculates all path positions reachable from the current player position,
        treating closed doors as walls.
        """
        queue = [(start_row, start_col)]
        visited = {(start_row, start_col)}

        while queue:
            r, c = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= self.maze.rows or nc < 0 or nc >= self.maze.cols:
                    continue
                if (nr, nc) in visited:
                    continue
                if not self.maze_is_path(nr, nc):
                    continue
                if self.door_manager and self.door_manager.is_door_locked_at(nr, nc):
                    continue
                visited.add((nr, nc))
                queue.append((nr, nc))

        return visited

    # =====================================================
    # START AND RESTART
    # =====================================================

    def start_game(
        self,
        level_id_or_diff,
    ):
        if level_id_or_diff in ("Easy", "Medium", "Hard"):
            level_map = {"Easy": "1-1", "Medium": "1-2", "Hard": "1-3"}
            self.selected_level_id = level_map[level_id_or_diff]
            difficulty = level_id_or_diff
        else:
            self.selected_level_id = level_id_or_diff
            difficulty = "Easy"

        self.selected_difficulty = difficulty
        self.difficulty_config = DIFFICULTY_SETTINGS.get(difficulty)

        # Apply theme for selected world level
        from game.levels import LevelManager
        lvl_config = LevelManager.get_level(self.selected_level_id)
        if lvl_config:
            self.selected_world_id = lvl_config.world_id
            world_config = LevelManager.get_world(self.selected_world_id)
            if world_config:
                self.selected_theme_name = world_config.theme_name
                from game.themes import ThemeManager
                ThemeManager.apply_theme(self.selected_theme_name)
                self.hud.theme_name = self.selected_theme_name
                self.save_data["selected_theme"] = self.selected_theme_name
                SaveManager.save(self.save_data)

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

        equipped_skin = self.save_data.get("selected_skin_by_world", {}).get(self.selected_world_id, "Shadow Ninja")
        equipped_accessory = self.save_data.get("selected_accessories_by_world", {}).get(self.selected_world_id, "Scarlet Scarf")
        equipped_colors = self.save_data.get("selected_colors_by_world", {}).get(self.selected_world_id, ((0, 0, 0), (245, 82, 95)))

        self.player.skin_name = equipped_skin
        self.player.accessory_name = equipped_accessory
        self.player.primary_color = equipped_colors[0]
        self.player.secondary_color = equipped_colors[1]

        # =================================================
        # CREATE POWER-UP MANAGER
        # =================================================
        import game.player
        game.player.PLAYER_MOVE_SPEED = 12.0
        from game.powerups import PowerUpManager
        self.powerup_manager = PowerUpManager(self.maze, self.fonts)
        self.powerup_manager.original_player_speed = 12.0
        self.powerup_manager.spawn_powerups(self, int(self.get_setting("powerup_count", 3)))

        # =================================================
        # CREATE TRAP MANAGER
        # =================================================
        from game.traps import TrapManager
        self.trap_manager = TrapManager(self.maze)
        self.trap_manager.spawn_traps(self, int(self.get_setting("trap_count", 5)))

        # =================================================
        # CREATE DOOR MANAGER
        # =================================================
        from game.doors import DoorManager
        self.door_manager = DoorManager(self.maze)
        self.door_manager.spawn_doors_and_keys(self, int(self.get_setting("door_count", 1)))

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
        if self.shadow_monster:
            self.shadow_monster.game = self

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
        self.slow_trap_timer = 0.0
        self.darkness_trap_timer = 0.0
        self.alarm_trap_timer = 0.0
        self.battery_leak_timer = 0.0
        self.teleport_flash = 0.0
        self.trap_immunity_timer = 0.0

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

        # Reset themed hazard variables
        self.cyber_glitch_timer = 0.0
        self.cyber_glitch_active = False
        self.desert_sandstorm_timer = 0.0
        self.desert_sandstorm_active = False
        self.slippery_ice_tiles = set()
        self.haunted_wall_tiles = set()
        self.haunted_wall_timer = 0.0
        self.lantern_positions = []
        self.spring_flower_positions = []

        if self.selected_theme_name == "Ninja World":
            self.lantern_positions = [(3, 3), (self.maze.rows - 4, 3), (3, self.maze.cols - 4), (self.maze.rows - 4, self.maze.cols - 4)]
            self.lantern_positions = [(r, c) for r, c in self.lantern_positions if self.maze_is_path(r, c)]
            self.maze.lanterns = self.lantern_positions
            
        elif self.selected_theme_name == "Spring World":
            candidates = []
            for r in range(1, self.maze.rows-1):
                for c in range(1, self.maze.cols-1):
                    if self.maze_is_path(r, c) and (r, c) != (self.player.row, self.player.col) and (r, c) != self.get_exit_position():
                        candidates.append((r, c))
            random.shuffle(candidates)
            self.spring_flower_positions = candidates[:5]
            
        elif self.selected_theme_name == "Frozen World":
            for r in range(1, self.maze.rows-1):
                for c in range(1, self.maze.cols-1):
                    if self.maze_is_path(r, c) and random.random() < 0.15:
                        self.slippery_ice_tiles.add((r, c))
                        
        elif self.selected_theme_name == "Haunted World":
            for r in range(1, self.maze.rows-1):
                for c in range(1, self.maze.cols-1):
                    if self.maze.grid[r][c] == 1 and random.random() < 0.08:
                        self.haunted_wall_tiles.add((r, c))

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
        self.trap_manager = None
        self.door_manager = None

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

            elif self.game_state == GAME_STATE_WORLD_SELECT:
                self.handle_world_select_event(event)

            elif self.game_state == GAME_STATE_LEVEL_SELECT:
                self.handle_level_select_event(event)

            elif self.game_state == GAME_STATE_CUSTOMIZATION:
                self.handle_customization_event(event)

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
            action_value = action[1] if len(action) > 1 else None
        else:
            action_name = action
            action_value = None

        if action_name == "continue":
            latest_unlocked = self.save_data.get("unlocked_levels", ["1-1"])[-1]
            self.start_transition(
                callback=lambda: self.start_game(latest_unlocked),
                transition_type="theme",
            )

        elif action_name == "select_world":
            self.world_select_screen = WorldSelectScreen(self.fonts, self.save_data)
            self.game_state = GAME_STATE_WORLD_SELECT

        elif action_name == "customize":
            self.customization_screen = CustomizationScreen(self.fonts, self.save_data, self.selected_world_id)
            self.game_state = GAME_STATE_CUSTOMIZATION

        elif action_name == "settings":
            if hasattr(self.hud, "show_notification"):
                self.hud.show_notification("Config toggles saved locally.")

        elif action_name == "how_to_play":
            if hasattr(self.hud, "show_notification"):
                self.hud.show_notification("Navigate with WASD/Arrows. Find the keys to unlock escape.")

        elif action_name in (
            "quit",
            "exit",
        ):
            self.running = False

    def handle_world_select_event(self, event):
        if not self.world_select_screen:
            return
        action = self.world_select_screen.handle_event(event)
        if action is None:
            return
        
        action_name, action_val = action
        if action_name == "change_theme":
            self.selected_theme_name = action_val
            from game.themes import ThemeManager
            ThemeManager.apply_theme(self.selected_theme_name)
            self.hud.theme_name = self.selected_theme_name
            self.save_data["selected_theme"] = self.selected_theme_name
            SaveManager.save(self.save_data)
        elif action_name == "select_world":
            self.selected_world_id = str(action_val)
            self.main_menu.selected_world_id = self.selected_world_id
            self.level_select_screen = LevelSelectScreen(self.fonts, self.save_data, self.selected_world_id)
            self.game_state = GAME_STATE_LEVEL_SELECT
        elif action_name == "back":
            self.game_state = GAME_STATE_MENU

    def handle_level_select_event(self, event):
        if not self.level_select_screen:
            return
        action = self.level_select_screen.handle_event(event)
        if action is None:
            return
            
        action_name, action_val = action
        if action_name == "start_level":
            self.start_transition(
                callback=lambda: self.start_game(action_val),
                transition_type="theme",
            )
        elif action_name == "back_to_worlds":
            self.world_select_screen = WorldSelectScreen(self.fonts, self.save_data)
            self.game_state = GAME_STATE_WORLD_SELECT

    def handle_customization_event(self, event):
        if not self.customization_screen:
            return
        action = self.customization_screen.handle_event(event)
        if action is None:
            return
            
        action_name, action_val = action
        if action_name == "equipped":
            SaveManager.save(self.save_data)
            # Sync menu equipped skin
            self.main_menu.save_data = self.save_data
            if hasattr(self.hud, "show_notification"):
                self.hud.show_notification("Character skin equipped!")
        elif action_name == "error_lock":
            if hasattr(self.hud, "show_notification"):
                self.hud.show_notification(action_val)
        elif action_name == "back":
            self.game_state = GAME_STATE_MENU

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

        elif action == "world_map":
            self.start_transition(
                callback=self.open_world_map_from_pause,
                transition_type="fade",
            )

        elif action == "settings":
            if hasattr(self.hud, "show_notification"):
                self.hud.show_notification("Sound settings auto-saved.")

        elif action == "menu":
            self.start_transition(
                callback=self.open_main_menu,
                transition_type="fade",
            )

    def open_world_map_from_pause(self):
        self.world_select_screen = WorldSelectScreen(self.fonts, self.save_data)
        self.game_state = GAME_STATE_WORLD_SELECT

    def handle_result_event(
        self,
        event,
    ):
        action = self.result_screen.handle_event(
            event
        )

        if action == "next_level":
            next_lvl = LevelManager.get_next_level_id(self.selected_level_id)
            if next_lvl:
                self.start_transition(
                    callback=lambda: self.start_game(next_lvl),
                    transition_type="theme",
                )

        elif action == "replay":
            self.start_transition(
                callback=self.restart_game,
                transition_type="fade",
            )

        elif action == "level_select":
            self.level_select_screen = LevelSelectScreen(self.fonts, self.save_data, self.selected_world_id)
            self.game_state = GAME_STATE_LEVEL_SELECT

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

        if transition_type == "theme":
            if hasattr(
                self.transition_manager,
                "start_theme",
            ):
                self.transition_manager.start_theme(
                    callback=callback,
                    theme_name=self.selected_theme_name
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

        # Cyber controls Glitch: reverse direction
        if getattr(self, "cyber_glitch_active", False):
            direction = (-direction[0], -direction[1])

        row_change, col_change = direction

        new_row = self.player.row + row_change
        new_col = self.player.col + col_change

        # Block move if stepping into a locked door
        if self.door_manager and self.door_manager.is_door_locked_at(new_row, new_col):
            self.door_manager.try_unlock_door(new_row, new_col, self)
            return

        # Ice sliding (Frozen World)
        if self.selected_theme_name == "Frozen World" and (new_row, new_col) in self.slippery_ice_tiles:
            curr_r, curr_c = new_row, new_col
            while True:
                next_r = curr_r + row_change
                next_c = curr_c + col_change
                if self.maze_is_path(next_r, next_c):
                    if self.door_manager and self.door_manager.is_door_locked_at(next_r, next_c):
                        break
                    curr_r, curr_c = next_r, next_c
                    if (curr_r, curr_c) not in self.slippery_ice_tiles:
                        break
                else:
                    break
            row_change = curr_r - self.player.row
            col_change = curr_c - self.player.col

        moved = self.player.try_move(
            row_change,
            col_change,
        )

        if moved:
            self.moves += 1

            self.movement_cooldown = (
                self.movement_delay
            )

            # Spring Flower pick up check
            if self.selected_theme_name == "Spring World":
                pr, pc = self.player.row, self.player.col
                if (pr, pc) in self.spring_flower_positions:
                    self.spring_flower_positions.remove((pr, pc))
                    self.battery_percentage = min(100.0, self.battery_percentage + 5.0)
                    self.hud.show_notification("+5% Battery (Spring Flower!)")
                    px, py = self.get_player_center()
                    self.particle_manager.create_burst(px, py, (140, 245, 150))

            self.check_battery_collection()
            if self.powerup_manager:
                self.powerup_manager.check_collisions(self)
            if self.trap_manager:
                self.trap_manager.check_player_cell(self)
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

        elif self.game_state == GAME_STATE_WORLD_SELECT:
            if self.world_select_screen:
                self.world_select_screen.update(delta_time)

        elif self.game_state == GAME_STATE_LEVEL_SELECT:
            if self.level_select_screen:
                self.level_select_screen.update(delta_time)

        elif self.game_state == GAME_STATE_CUSTOMIZATION:
            if self.customization_screen:
                self.customization_screen.update(delta_time)

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

        # Haunted walls shifting
        if self.selected_theme_name == "Haunted World":
            self.haunted_wall_timer += delta_time
            if self.haunted_wall_timer >= 4.0:
                self.haunted_wall_timer = 0.0
                for wr, wc in self.haunted_wall_tiles:
                    self.maze.grid[wr][wc] = 1 - self.maze.grid[wr][wc]
                self.hud.show_notification("Ghost walls shifted!")

        # Cyber controls glitch
        if self.selected_theme_name == "Cyber World":
            self.cyber_glitch_timer += delta_time
            if not self.cyber_glitch_active:
                if self.cyber_glitch_timer >= 12.0:
                    self.cyber_glitch_active = True
                    self.cyber_glitch_timer = 0.0
                    self.hud.show_notification("GLITCH: Controls Reversed!")
            else:
                if self.cyber_glitch_timer >= 3.0:
                    self.cyber_glitch_active = False
                    self.cyber_glitch_timer = 0.0
                    self.hud.show_notification("Glitch resolved.")

        self.movement_cooldown = max(
            0,
            self.movement_cooldown
            - delta_time,
        )

        self.screen_flash = max(0.0, self.screen_flash - delta_time)

        # Count down trap effect timers
        self.slow_trap_timer = max(0.0, self.slow_trap_timer - delta_time)
        self.darkness_trap_timer = max(0.0, self.darkness_trap_timer - delta_time)
        self.alarm_trap_timer = max(0.0, self.alarm_trap_timer - delta_time)
        self.battery_leak_timer = max(0.0, self.battery_leak_timer - delta_time)
        self.teleport_flash = max(0.0, self.teleport_flash - delta_time)
        self.trap_immunity_timer = max(0.0, self.trap_immunity_timer - delta_time)

        if self.shadow_monster:
            self.shadow_monster.alarm_active = (self.alarm_trap_timer > 0.0)

        # Calculate final speed multiplier
        base_speed = 12.0
        powerup_mult = 1.40 if (self.powerup_manager and self.powerup_manager.is_active("Speed")) else 1.0
        trap_mult = 0.55 if self.slow_trap_timer > 0.0 else 1.0

        import game.player
        game.player.PLAYER_MOVE_SPEED = base_speed * powerup_mult * trap_mult

        if self.powerup_manager:
            self.powerup_manager.update(delta_time, self)
            self.powerup_manager.check_collisions(self)

        if self.trap_manager:
            self.trap_manager.update(delta_time, self)

        if self.door_manager:
            self.door_manager.update(delta_time, self)

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

        if getattr(self, "battery_leak_timer", 0.0) > 0.0:
            drain_rate += 2.0  # Extra drain of 2.0% per second during leak trap

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

        super_torch_bonus = 3 if (self.powerup_manager and self.powerup_manager.is_active("Torch")) else 0
        darkness_penalty = 2 if getattr(self, "darkness_trap_timer", 0.0) > 0.0 else 0

        final_visibility = radius + super_torch_bonus - darkness_penalty
        return max(1, final_visibility)

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

        # Check if all doors are unlocked
        if self.door_manager and not self.door_manager.all_doors_unlocked():
            if hasattr(self.hud, "show_notification"):
                self.hud.show_notification("Escape Locked! Unlock all doors first.")
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

        # Calculate score, stars, unlock next level & cosmetics
        lvl_id = self.selected_level_id
        lvl_config = LevelManager.get_level(lvl_id)
        
        stars = 1
        if lvl_config:
            time_ok = (self.elapsed_time <= lvl_config.time_target)
            moves_ok = (self.moves <= lvl_config.move_target)
            battery_ok = (self.battery_percentage >= 25.0)
            
            if time_ok and moves_ok and battery_ok:
                stars = 3
            elif time_ok or moves_ok:
                stars = 2

        # Save records in progress profile
        prev_hi = self.save_data.get("highest_score", {}).get(lvl_id, 0)
        new_record = False
        if self.final_score > prev_hi:
            self.save_data["highest_score"][lvl_id] = self.final_score
            new_record = True
            
        prev_time = self.save_data.get("best_time", {}).get(lvl_id, 99999)
        if self.elapsed_time < prev_time:
            self.save_data["best_time"][lvl_id] = int(self.elapsed_time)
            
        prev_moves = self.save_data.get("best_moves", {}).get(lvl_id, 99999)
        if self.moves < prev_moves:
            self.save_data["best_moves"][lvl_id] = self.moves

        prev_stars = self.save_data.get("stars_earned", {}).get(lvl_id, 0)
        if stars > prev_stars:
            self.save_data["stars_earned"][lvl_id] = stars

        if lvl_id not in self.save_data.get("completed_levels", []):
            self.save_data["completed_levels"].append(lvl_id)

        # Unlock next level
        next_lvl_id = LevelManager.get_next_level_id(lvl_id)
        if next_lvl_id and next_lvl_id not in self.save_data.get("unlocked_levels", []):
            self.save_data["unlocked_levels"].append(next_lvl_id)

        # Cosmetic unlocks
        unlocked_reward = None
        if lvl_config and lvl_config.is_boss_level:
            boss_rewards = {
                "1": "Masked Kunoichi",
                "2": "Nature Guardian",
                "3": "Crystal Knight",
                "4": "Victorian Explorer",
                "5": "Robot Scout",
                "6": "Temple Explorer",
            }
            reward = boss_rewards.get(lvl_config.world_id)
            if reward and reward not in self.save_data.get("unlocked_skins", []):
                self.save_data["unlocked_skins"].append(reward)
                unlocked_reward = reward
        else:
            level_rewards = {
                "1-2": "Crimson Ninja",
                "1-3": "Blue Moon Ninja",
                "1-4": "White Ronin",
                "2-2": "Flower Mage",
                "2-3": "Butterfly Knight",
                "2-4": "Garden Fairy",
                "3-2": "Snow Scout",
                "3-3": "Frost Mage",
                "3-4": "Arctic Explorer",
                "4-2": "Little Witch",
                "4-3": "Skeleton Hero",
                "4-4": "Cursed Knight",
                "5-2": "Neon Hacker",
                "5-3": "Battle Android",
                "5-4": "Glitch Runner",
                "6-2": "Desert Guardian",
                "6-3": "Pharaoh Warrior",
                "6-4": "Sand Mage",
            }
            reward = level_rewards.get(lvl_id)
            if reward and reward not in self.save_data.get("unlocked_skins", []):
                self.save_data["unlocked_skins"].append(reward)
                unlocked_reward = reward

        # Persist save profile
        SaveManager.save(self.save_data)

        # Show result screen
        self.game_state = GAME_STATE_WON
        self.result_screen.open(
            difficulty=self.selected_difficulty,
            moves=self.moves,
            elapsed_seconds=int(self.elapsed_time),
            battery=self.battery_percentage,
            score=self.final_score,
            level_id=lvl_id,
            has_next_level=(next_lvl_id is not None),
            stars_earned=stars,
            new_record=new_record,
            unlocked_rewards=unlocked_reward,
        )

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

        elif self.game_state == GAME_STATE_WORLD_SELECT:
            if self.world_select_screen:
                self.world_select_screen.draw(self.screen)

        elif self.game_state == GAME_STATE_LEVEL_SELECT:
            if self.level_select_screen:
                self.level_select_screen.draw(self.screen)

        elif self.game_state == GAME_STATE_CUSTOMIZATION:
            if self.customization_screen:
                self.customization_screen.draw(self.screen)

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

        # 1. Clear background to pitch black
        self.screen.fill((0, 0, 0))

        visibility_radius = (
            self.get_visibility_radius()
        )

        # 2. Draw maze world
        self.draw_maze(
            visibility_radius
        )

        # 3. Draw exit & batteries
        self.draw_exit(
            visibility_radius
        )

        self.draw_batteries(
            visibility_radius
        )

        # 4. Draw world theme elements
        self.draw_world_theme_elements(visibility_radius)

        # 5. Draw powerups, traps, doors
        if self.powerup_manager:
            self.powerup_manager.draw(self.screen)

        if self.trap_manager:
            self.trap_manager.draw(
                self.screen,
                self.player.row,
                self.player.col,
                visibility_radius,
            )

        if self.door_manager:
            self.door_manager.draw(
                self.screen,
                visibility_radius,
                self.player.row,
                self.player.col,
            )

        # 6. Draw monster & particles
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

        # 7. Draw player character
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

        # 8. Apply Darkness Mask / Torch Effect centered on player's smooth pixel position (player.x, player.y)
        px, py = self.player.x, self.player.y
        torch_r = self.maze.cell_size * (visibility_radius + 0.6)

        # Low battery flickering
        if self.battery_percentage < 20.0:
            torch_r += random.uniform(-3.5, 3.5)

        self.torch_renderer.apply(
            self.screen,
            px=px,
            py=py,
            radius=max(20.0, torch_r),
            theme_name=self.selected_theme_name,
        )

        # 9. Draw trap / damage flashes
        if getattr(self, "slow_trap_timer", 0.0) > 0.0:
            self.draw_slow_trap_puddle()

        if getattr(self, "darkness_trap_timer", 0.0) > 0.0:
            self.draw_darkness_vignette()

        self.draw_teleport_flash()
        self.draw_screen_flash()
        self.draw_monster_damage_flash()

        # 10. Draw HUD last (bright & unmasked)
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

    def draw_slow_trap_puddle(self):
        px, py = self.get_player_center()
        # Draw a sticky puddle under player
        puddle_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(puddle_surf, (20, 10, 30, 160), (0, 10, 40, 20))
        self.screen.blit(puddle_surf, (px - 20, py - 20))
        # Draw a dark sticky chain line
        pygame.draw.line(self.screen, (40, 30, 50), (px - 12, py + 5), (px + 12, py + 5), width=3)

    def draw_darkness_vignette(self):
        if getattr(self, "darkness_vignette_surface", None) is None:
            w, h = SCREEN_WIDTH, SCREEN_HEIGHT
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            # Create a retro fading dark vignette
            for i in range(12):
                alpha = int(180 * (i / 12) ** 2)
                inset_x = int(w * 0.40 * (1 - i / 12))
                inset_y = int(h * 0.40 * (1 - i / 12))
                rect = pygame.Rect(inset_x, inset_y, w - inset_x * 2, h - inset_y * 2)
                pygame.draw.rect(surf, (0, 0, 0, alpha), rect, width=25)
            self.darkness_vignette_surface = surf
        self.screen.blit(self.darkness_vignette_surface, (0, 0))

    def draw_teleport_flash(self):
        if getattr(self, "teleport_flash", 0.0) <= 0:
            return
        alpha = int(120 * (self.teleport_flash / 0.25))
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((160, 32, 240, alpha))
        self.screen.blit(surf, (0, 0))

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

    def draw_world_theme_elements(self, visibility_radius):
        if self.selected_theme_name == "Ninja World":
            for lr, lc in self.lantern_positions:
                if self.maze.is_cell_visible(lr, lc, self.player.row, self.player.col, visibility_radius) or self.maze.was_visited(lr, lc):
                    cx, cy = self.maze.get_cell_center(lr, lc)
                    pygame.draw.circle(self.screen, (255, 140, 0), (cx, cy), 10)
                    pygame.draw.circle(self.screen, (255, 230, 110), (cx, cy), 10, width=2)
                    glow = pygame.Surface((60, 60), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (255, 180, 50, 45), (30, 30), 30)
                    self.screen.blit(glow, (cx - 30, cy - 30))

        elif self.selected_theme_name == "Spring World":
            for fr, fc in self.spring_flower_positions:
                if self.maze.is_cell_visible(fr, fc, self.player.row, self.player.col, visibility_radius):
                    cx, cy = self.maze.get_cell_center(fr, fc)
                    pygame.draw.circle(self.screen, (255, 105, 180), (cx, cy), 8)
                    for angle in range(0, 360, 72):
                        rad = math.radians(angle)
                        px = cx + int(math.cos(rad) * 9)
                        py = cy + int(math.sin(rad) * 9)
                        pygame.draw.circle(self.screen, (255, 182, 193), (px, py), 5)
                    pygame.draw.circle(self.screen, (255, 215, 0), (cx, cy), 4)

        elif self.selected_theme_name == "Frozen World":
            for ir, ic in self.slippery_ice_tiles:
                if self.maze.is_cell_visible(ir, ic, self.player.row, self.player.col, visibility_radius):
                    rect = self.maze.get_cell_rect(ir, ic)
                    ice_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    ice_surf.fill((140, 220, 255, 80))
                    pygame.draw.line(ice_surf, (255, 255, 255, 150), (rect.width//2, 4), (rect.width//2, rect.height-4), 2)
                    pygame.draw.line(ice_surf, (255, 255, 255, 150), (4, rect.height//2), (rect.width-4, rect.height//2), 2)
                    self.screen.blit(ice_surf, rect.topleft)

        if self.selected_theme_name == "Desert Temple World":
            sand_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            opacity = int(12 + math.sin(time.time() * 2.0) * 6)
            sand_surf.fill((210, 180, 140, opacity))
            self.screen.blit(sand_surf, (0, 0))

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
                active_traps={
                    "SLOWED": self.slow_trap_timer,
                    "DARKNESS": self.darkness_trap_timer,
                    "ALARM": self.alarm_trap_timer,
                    "BATTERY LEAK": self.battery_leak_timer,
                },
                remaining_traps=(
                    self.trap_manager.get_remaining_count()
                    if self.trap_manager
                    else None
                ),
                inventory=(
                    self.door_manager.inventory
                    if self.door_manager
                    else None
                ),
                remaining_doors=(
                    self.door_manager.get_remaining_count()
                    if self.door_manager
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

        all_unlocked = True
        if self.door_manager and not self.door_manager.all_doors_unlocked():
            all_unlocked = False

        pulse_value = (
            math.sin(
                pygame.time.get_ticks()
                * 0.006
            )
            + 1
        ) / 2

        if all_unlocked:
            outer_radius = int(
                self.maze.cell_size
                * (
                    0.40
                    + pulse_value * 0.12
                )
            )

            inner_radius = max(
                5,
                int(
                    outer_radius
                    * 0.60
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
                    50,
                ),
                (
                    center_x,
                    center_y,
                ),
                outer_radius + 18,
            )

            pygame.draw.circle(
                glow_surface,
                (
                    EXIT_COLOR[0],
                    EXIT_COLOR[1],
                    EXIT_COLOR[2],
                    80,
                ),
                (
                    center_x,
                    center_y,
                ),
                outer_radius + 9,
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
                    3,
                    self.maze.cell_size // 8,
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
        else:
            outer_radius = int(self.maze.cell_size * 0.22)
            inner_radius = 4

            glow_surface = pygame.Surface(
                self.screen.get_size(),
                pygame.SRCALPHA,
            )

            pygame.draw.circle(
                glow_surface,
                (45, 60, 50, 20),
                (
                    center_x,
                    center_y,
                ),
                outer_radius + 6,
            )

            self.screen.blit(
                glow_surface,
                (0, 0),
            )

            pygame.draw.circle(
                self.screen,
                (70, 85, 75),
                (
                    center_x,
                    center_y,
                ),
                outer_radius,
                width=2,
            )

            pygame.draw.circle(
                self.screen,
                (45, 55, 50),
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