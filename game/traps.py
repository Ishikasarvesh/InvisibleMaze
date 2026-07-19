import math
import random
import pygame
from game.settings import RED, YELLOW, PANEL, PANEL_BORDER, SCREEN_WIDTH, SCREEN_HEIGHT

class Trap:
    """
    Represents one individual hidden trap in the maze.
    """

    def __init__(self, row, col, trap_type):
        self.row = row
        self.col = col
        self.type = trap_type  # "Spike", "Slow", "Darkness", "Alarm", "Teleport", "BatteryLeak"

        self.is_triggered = False
        self.is_disabled = False
        self.animation_time = 0.0
        self.animation_duration = 0.90  # Trap trigger animation length

    def update(self, delta_time, game):
        """
        Updates the active trap's animation and spawns trap-specific particles.
        """
        if self.is_triggered and not self.is_disabled:
            self.animation_time += delta_time
            if self.animation_time >= self.animation_duration:
                self.is_disabled = True

            # Spawn particles while triggered and animating
            cx, cy = game.maze.get_cell_center(self.row, self.col)
            if self.type == "Spike" and random.random() < 0.35:
                if hasattr(game.particle_manager, "create_red_sparks"):
                    game.particle_manager.create_red_sparks(cx, cy)
            elif self.type == "Darkness" and random.random() < 0.35:
                if hasattr(game.particle_manager, "create_smoke_ring"):
                    game.particle_manager.create_smoke_ring(cx, cy)
            elif self.type == "Teleport" and random.random() < 0.35:
                if hasattr(game.particle_manager, "create_teleport_burst"):
                    game.particle_manager.create_teleport_burst(cx, cy)
            elif self.type == "BatteryLeak" and random.random() < 0.35:
                if hasattr(game.particle_manager, "create_battery_sparks"):
                    game.particle_manager.create_battery_sparks(cx, cy)

    def draw_warning(self, surface, maze, anim_time):
        """
        Draws a subtle warning (tiny cracks + low opacity red pulse) when the player is nearby.
        """
        cx, cy = maze.get_cell_center(self.row, self.col)
        size = maze.cell_size

        # Faint red pulsing glow
        pulse_val = (math.sin(anim_time * 5.0) + 1.0) / 2.0
        alpha = int(12 + pulse_val * 18)  # Maximum opacity of 30 for high subtlety

        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (220, 30, 40, alpha), (size // 2, size // 2), size // 2)
        surface.blit(glow_surf, (cx - size // 2, cy - size // 2))

        # Tiny red floor crack line
        pygame.draw.line(surface, (180, 40, 40, 80), (cx - 4, cy - 2), (cx + 3, cy + 2), width=1)
        pygame.draw.line(surface, (180, 40, 40, 80), (cx + 2, cy - 3), (cx - 3, cy + 3), width=1)

    def draw_active(self, surface, maze):
        """
        Draws the trap trigger animation.
        """
        cx, cy = maze.get_cell_center(self.row, self.col)
        size = maze.cell_size
        t_ratio = min(1.0, self.animation_time / self.animation_duration)

        if self.type == "Spike":
            # Drawing a base plate and spikes popping up
            pygame.draw.rect(surface, (80, 80, 85), (cx - size // 3, cy - size // 3, size * 2 // 3, size * 2 // 3))
            y_offset = int(t_ratio * (size // 3))
            pygame.draw.polygon(surface, (190, 190, 200), [(cx - 8, cy + 4 - y_offset), (cx - 5, cy - 8 - y_offset), (cx - 2, cy + 4 - y_offset)])
            pygame.draw.polygon(surface, (190, 190, 200), [(cx - 3, cy + 4 - y_offset), (cx, cy - 10 - y_offset), (cx + 3, cy + 4 - y_offset)])
            pygame.draw.polygon(surface, (190, 190, 200), [(cx + 2, cy + 4 - y_offset), (cx + 5, cy - 8 - y_offset), (cx + 8, cy + 4 - y_offset)])

        elif self.type == "Slow":
            # Sticky tar pool expanding
            rad = int((size // 3.5) * (1.0 + t_ratio))
            pygame.draw.circle(surface, (20, 10, 30), (cx, cy), rad)
            pygame.draw.circle(surface, (50, 35, 70), (cx, cy), rad, width=2)

        elif self.type == "Darkness":
            # Expanding dark smoke ring
            rad = int((size // 2.5) * t_ratio)
            if rad > 1:
                pygame.draw.circle(surface, (10, 10, 15), (cx, cy), rad, width=3)

        elif self.type == "Alarm":
            # Red warning circle rune
            rad = int(size // 3)
            pygame.draw.circle(surface, (240, 45, 55), (cx, cy), rad, width=2)
            pygame.draw.circle(surface, (240, 45, 55), (cx, cy), max(2, int(rad * (1.0 - t_ratio))))

        elif self.type == "Teleport":
            # Purple portal ring
            rad = int((size // 3) * (1.0 - t_ratio))
            if rad > 1:
                pygame.draw.circle(surface, (160, 32, 240), (cx, cy), rad, width=2)

        elif self.type == "BatteryLeak":
            # Yellow electrical crack
            pygame.draw.line(surface, YELLOW, (cx - 6, cy - 8), (cx + 2, cy - 2), width=2)
            pygame.draw.line(surface, YELLOW, (cx + 2, cy - 2), (cx - 4, cy + 4), width=2)
            pygame.draw.line(surface, YELLOW, (cx - 4, cy + 4), (cx + 4, cy + 8), width=2)

    def draw_disabled(self, surface, maze):
        """
        Draws the spent/disabled trap on the floor.
        """
        cx, cy = maze.get_cell_center(self.row, self.col)
        size = maze.cell_size

        if self.type == "Spike":
            pygame.draw.rect(surface, (55, 55, 60), (cx - size // 3, cy - size // 3, size * 2 // 3, size * 2 // 3), width=1)
        elif self.type == "Slow":
            pygame.draw.circle(surface, (20, 12, 25), (cx, cy), size // 4, width=1)
        elif self.type == "Darkness":
            pygame.draw.circle(surface, (15, 15, 20), (cx, cy), 3)
        elif self.type == "Alarm":
            pygame.draw.circle(surface, (100, 30, 35), (cx, cy), size // 4, width=1)
        elif self.type == "Teleport":
            pygame.draw.circle(surface, (80, 20, 110), (cx, cy), size // 4, width=1)
        elif self.type == "BatteryLeak":
            pygame.draw.line(surface, (110, 95, 30), (cx - 4, cy - 4), (cx + 4, cy + 4), width=1)


class TrapManager:
    """
    Generates, updates, and checks collisions for Hidden Traps.
    """

    def __init__(self, maze):
        self.maze = maze
        self.traps = []
        self.traps_by_position = {}

    def spawn_traps(self, game, count):
        """
        Spawns untriggered traps in valid maze path positions.
        """
        self.traps.clear()
        self.traps_by_position.clear()

        # Get positions to avoid
        player_row, player_col = game.get_start_position()
        exit_row, exit_col = game.get_exit_position()

        monster_row, monster_col = -1, -1
        if game.shadow_monster:
            monster_row = game.shadow_monster.row
            monster_col = game.shadow_monster.col

        # Exclude player starting cell and its neighbors
        player_neighbors = [
            (player_row, player_col),
            (player_row - 1, player_col),
            (player_row + 1, player_col),
            (player_row, player_col - 1),
            (player_row, player_col + 1),
        ]
        avoid_cells = set(player_neighbors)
        avoid_cells.add((exit_row, exit_col))
        avoid_cells.add((monster_row, monster_col))

        # Exclude battery pickups
        if game.battery_manager and hasattr(game.battery_manager, "pickups"):
            for b in game.battery_manager.pickups:
                avoid_cells.add((b.row, b.col))

        # Exclude mystery power-ups
        if game.powerup_manager and hasattr(game.powerup_manager, "spawned_powerups"):
            for p in game.powerup_manager.spawned_powerups:
                avoid_cells.add((p.row, p.col))

        possible_positions = []
        for r in range(1, self.maze.rows - 1):
            for c in range(1, self.maze.cols - 1):
                if not game.maze_is_path(r, c):
                    continue
                if (r, c) in avoid_cells:
                    continue
                possible_positions.append((r, c))

        if not possible_positions:
            return

        spawn_count = min(count, len(possible_positions))
        selected_positions = random.sample(possible_positions, spawn_count)

        trap_types = ["Spike", "Slow", "Darkness", "Alarm", "Teleport", "BatteryLeak"]

        for r, c in selected_positions:
            ttype = random.choice(trap_types)
            t = Trap(r, c, ttype)
            self.traps.append(t)
            self.traps_by_position[(r, c)] = t

    def update(self, delta_time, game):
        """
        Updates active trap animations.
        """
        for t in self.traps:
            t.update(delta_time, game)

    def draw(self, surface, player_row, player_col, visibility_radius):
        """
        Draws traps and subtle warnings when near untriggered traps.
        """
        anim_time = pygame.time.get_ticks() / 1000.0

        for t in self.traps:
            dist = abs(t.row - player_row) + abs(t.col - player_col)

            if not t.is_triggered:
                # Draw warning crack if within 1 cell and visible
                if dist <= 1 and dist <= visibility_radius:
                    t.draw_warning(surface, self.maze, anim_time)
            else:
                # Draw triggered or disabled traps
                if dist <= visibility_radius + 1:
                    if not t.is_disabled:
                        t.draw_active(surface, self.maze)
                    else:
                        t.draw_disabled(surface, self.maze)

    def check_player_cell(self, game):
        """
        Triggers trap activation if player steps on a trap cell and has no immunity.
        """
        if getattr(game, "trap_immunity_timer", 0.0) > 0.0:
            return

        p_row = game.player.row
        p_col = game.player.col

        trap = self.traps_by_position.get((p_row, p_col))
        if trap and not trap.is_triggered and not trap.is_disabled:
            trap.is_triggered = True
            game.trap_immunity_timer = 1.0  # Set global trap immunity
            self.activate_trap(trap, game)

    def activate_trap(self, trap, game):
        """
        Applies specific trap effects upon trigger.
        """
        # Sound hook placeholder
        # print(f"[Sound Hook] Play trap trigger sound for {trap.type}")

        if trap.type == "Spike":
            game.battery_percentage = max(0.0, game.battery_percentage - 15.0)
            game.monster_hit_flash = 0.35  # Screen flash red overlay
            game.player.play_wall_hit_animation()  # Shake player
            if hasattr(game.hud, "show_notification"):
                game.hud.show_notification("Spike Trap! -15% Battery")

        elif trap.type == "Slow":
            game.slow_trap_timer = 6.0
            if hasattr(game.hud, "show_notification"):
                game.hud.show_notification("You are slowed!")

        elif trap.type == "Darkness":
            game.darkness_trap_timer = 7.0
            if hasattr(game.hud, "show_notification"):
                game.hud.show_notification("Darkness surrounds you!")

        elif trap.type == "Alarm":
            game.alarm_trap_timer = 8.0
            if game.shadow_monster:
                game.shadow_monster.alarm_active = True
                game.shadow_monster.move_timer = 0.0  # Immediately recalculate route
            if hasattr(game.hud, "show_notification"):
                game.hud.show_notification("The Shadow has found you!")

        elif trap.type == "Teleport":
            self.teleport_player(game)

        elif trap.type == "BatteryLeak":
            game.battery_leak_timer = 8.0
            if hasattr(game.hud, "show_notification"):
                game.hud.show_notification("Battery leaking!")

    def teleport_player(self, game):
        """
        Teleports player to a random path cell at least 6 cells away.
        """
        p_row, p_col = game.player.row, game.player.col

        # Disappearance particles
        cx_old, cy_old = game.maze.get_cell_center(p_row, p_col)
        if hasattr(game.particle_manager, "create_teleport_burst"):
            game.particle_manager.create_teleport_burst(cx_old, cy_old)

        # Collect positions to avoid
        avoid_cells = set()
        exit_row, exit_col = game.get_exit_position()
        avoid_cells.add((exit_row, exit_col))
        
        if game.shadow_monster:
            avoid_cells.add((game.shadow_monster.row, game.shadow_monster.col))

        for t in self.traps:
            if not t.is_disabled:
                avoid_cells.add((t.row, t.col))

        if game.battery_manager and hasattr(game.battery_manager, "pickups"):
            for b in game.battery_manager.pickups:
                avoid_cells.add((b.row, b.col))

        if game.powerup_manager and hasattr(game.powerup_manager, "spawned_powerups"):
            for p in game.powerup_manager.spawned_powerups:
                if not p.collected:
                    avoid_cells.add((p.row, p.col))

        possible_positions = []
        for r in range(1, self.maze.rows - 1):
            for c in range(1, self.maze.cols - 1):
                if not game.maze_is_path(r, c):
                    continue
                # Distance must be at least 6 cells
                dist = abs(r - p_row) + abs(c - p_col)
                if dist < 6:
                    continue
                if (r, c) in avoid_cells:
                    continue
                possible_positions.append((r, c))

        if not possible_positions:
            # Fallback to any path cell at least 6 away
            for r in range(1, self.maze.rows - 1):
                for c in range(1, self.maze.cols - 1):
                    if not game.maze_is_path(r, c):
                        continue
                    if abs(r - p_row) + abs(c - p_col) >= 6:
                        possible_positions.append((r, c))

        if possible_positions:
            dest_row, dest_col = random.choice(possible_positions)

            # Teleport player
            game.player.row = dest_row
            game.player.col = dest_col
            cx, cy = game.maze.get_cell_center(dest_row, dest_col)
            game.player.x = float(cx)
            game.player.y = float(cy)
            game.player.target_x = float(cx)
            game.player.target_y = float(cy)
            game.player.is_moving = False

            # Screen purple flash
            game.teleport_flash = 0.25

            # Appearance particles
            if hasattr(game.particle_manager, "create_teleport_burst"):
                game.particle_manager.create_teleport_burst(cx, cy)

            if hasattr(game.hud, "show_notification"):
                game.hud.show_notification("Lost in the darkness...")

            # Run interaction checks at target
            game.check_battery_collection()
            if game.powerup_manager:
                game.powerup_manager.check_collisions(game)
            game.check_win_condition()

    def get_remaining_count(self):
        """
        Returns number of untriggered traps.
        """
        return sum(1 for t in self.traps if not t.is_disabled)
