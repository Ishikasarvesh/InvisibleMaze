import math
import random
import pygame
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL, PANEL_BORDER, YELLOW, WHITE, TEXT_MUTED, BLUE, GREEN, ORANGE, RED

class Key:
    """
    Represents a collectible key of a specific color.
    """

    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color  # "Red", "Blue", "Green", "Gold"
        self.collected = False
        self.angle = random.uniform(0, 360)
        self.bounce_offset = random.uniform(0, math.tau)
        self.anim_time = 0.0

    def update(self, delta_time):
        """
        Updates rotation and float animations for the key.
        """
        if not self.collected:
            self.anim_time += delta_time
            self.angle = (self.angle + delta_time * 90.0) % 360.0

    def draw(self, surface, maze, visibility_radius, player_row, player_col):
        """
        Draws the floating, rotating key when within range.
        """
        if self.collected:
            return

        dist = abs(self.row - player_row) + abs(self.col - player_col)
        if dist > visibility_radius:
            return

        cx, cy = maze.get_cell_center(self.row, self.col)
        size = maze.cell_size

        # Floating bounce animation
        bounce = math.sin(self.anim_time * 4.0 + self.bounce_offset) * (size // 6)
        y_pos = cy + bounce

        # Color mapping
        rgb = (255, 255, 255)
        if self.color == "Red": rgb = (245, 82, 95)
        elif self.color == "Blue": rgb = (89, 145, 255)
        elif self.color == "Green": rgb = (69, 230, 154)
        elif self.color == "Gold": rgb = (255, 215, 0)

        # Draw glow
        glow_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (rgb[0], rgb[1], rgb[2], 30), (size, size), size)
        surface.blit(glow_surf, (cx - size, int(y_pos) - size))

        # Render key shape
        # Head (Circle)
        pygame.draw.circle(surface, rgb, (cx, int(y_pos - 3)), 5, width=2)
        # Shaft
        pygame.draw.line(surface, rgb, (cx, int(y_pos + 2)), (cx, int(y_pos + 10)), width=2)
        # Teeth
        pygame.draw.line(surface, rgb, (cx, int(y_pos + 6)), (cx + 3, int(y_pos + 6)), width=2)
        pygame.draw.line(surface, rgb, (cx, int(y_pos + 9)), (cx + 3, int(y_pos + 9)), width=2)


class Door:
    """
    Represents a locked color barrier blocking paths.
    """

    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color  # "Red", "Blue", "Green", "Gold"
        self.is_locked = True
        self.is_open = False
        self.animation_time = 0.0
        self.animation_duration = 0.90  # 0.90s dissolve unlock animation

    def update(self, delta_time, game):
        """
        Updates the door's cracking/dissolving transition upon unlocking.
        """
        if not self.is_locked and not self.is_open:
            self.animation_time += delta_time
            if self.animation_time >= self.animation_duration:
                self.is_open = True

            # Spawning unlocking shards
            cx, cy = game.maze.get_cell_center(self.row, self.col)
            if random.random() < 0.35:
                if hasattr(game.particle_manager, "create_unlock_shards"):
                    game.particle_manager.create_unlock_shards(cx, cy, self.color)

    def draw(self, surface, maze, visibility_radius, player_row, player_col):
        """
        Draws the glowing barrier (or dissolving segments if unlocking).
        """
        if self.is_open:
            return

        dist = abs(self.row - player_row) + abs(self.col - player_col)
        if dist > visibility_radius + 1:
            return

        cx, cy = maze.get_cell_center(self.row, self.col)
        size = maze.cell_size

        # Color mapping
        rgb = (255, 255, 255)
        if self.color == "Red": rgb = (245, 82, 95)
        elif self.color == "Blue": rgb = (89, 145, 255)
        elif self.color == "Green": rgb = (69, 230, 154)
        elif self.color == "Gold": rgb = (255, 215, 0)

        # Pulse energy field
        pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1.0) / 2.0

        if self.is_locked:
            # Draw barrier glow
            glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            alpha = int(45 + pulse * 45)
            glow_surf.fill((rgb[0], rgb[1], rgb[2], alpha))
            surface.blit(glow_surf, (cx - size // 2, cy - size // 2))

            # Barrier outline
            pygame.draw.rect(surface, rgb, (cx - size // 2, cy - size // 2, size, size), width=3)
            
            # Floating lock symbol
            pygame.draw.rect(surface, (20, 20, 20), (cx - 5, cy - 1, 10, 8))
            pygame.draw.circle(surface, rgb, (cx, cy - 1), 4, width=2)
            pygame.draw.rect(surface, rgb, (cx - 5, cy - 1, 10, 8), width=1)
        else:
            # Dissolve cracking animation
            progress = min(1.0, self.animation_time / self.animation_duration)
            alpha = int(80 * (1.0 - progress))

            glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            glow_surf.fill((rgb[0], rgb[1], rgb[2], alpha))
            surface.blit(glow_surf, (cx - size // 2, cy - size // 2))

            # Fractured outlines
            thickness = max(1, int(3 * (1.0 - progress)))
            pygame.draw.rect(surface, rgb, (cx - size // 2, cy - size // 2, size, size), width=thickness)


class DoorManager:
    """
    Handles key/door placements, checks inventory constraints, and verifies solvability.
    """

    def __init__(self, maze):
        self.maze = maze
        self.doors = []
        self.keys = []
        self.doors_by_position = {}
        self.keys_by_position = {}
        self.inventory = {
            "Red": 0,
            "Blue": 0,
            "Green": 0,
            "Gold": 0,
        }
        self.exit_triggered = False

    def reset(self):
        """
        Clears all inventories and placements.
        """
        self.doors.clear()
        self.keys.clear()
        self.doors_by_position.clear()
        self.keys_by_position.clear()
        self.inventory = {
            "Red": 0,
            "Blue": 0,
            "Green": 0,
            "Gold": 0,
        }
        self.exit_triggered = False

    def all_doors_unlocked(self):
        """
        Returns true if all spawned doors are unlocked.
        """
        if not self.doors:
            return True
        return all(not d.is_locked for d in self.doors)

    def is_door_locked_at(self, row, col):
        """
        Helper for movement/monster checks.
        """
        door = self.doors_by_position.get((row, col))
        if door:
            return door.is_locked
        return False

    def is_door_at(self, row, col):
        return (row, col) in self.doors_by_position

    def is_key_at(self, row, col):
        return (row, col) in self.keys_by_position

    def get_remaining_count(self):
        """
        Returns total locked doors.
        """
        return sum(1 for d in self.doors if d.is_locked)

    def update(self, delta_time, game):
        """
        Updates timers and verifies key pick-ups.
        """
        for d in self.doors:
            d.update(delta_time, game)
        for k in self.keys:
            k.update(delta_time)

        # Check key collection
        p_row, p_col = game.player.row, game.player.col
        key = self.keys_by_position.get((p_row, p_col))
        if key and not key.collected:
            self.collect_key(key, game)

        # Check exit unlock trigger
        if self.all_doors_unlocked() and not self.exit_triggered:
            self.exit_triggered = True
            ex_row, ex_col = game.get_exit_position()
            cx, cy = game.maze.get_cell_center(ex_row, ex_col)
            if hasattr(game.particle_manager, "create_exit_explosion"):
                game.particle_manager.create_exit_explosion(cx, cy)
            if hasattr(game.hud, "show_notification"):
                game.hud.show_notification("The exit has opened!")

    def draw(self, surface, visibility_radius, player_row, player_col):
        """
        Renders all doors and keys in range.
        """
        for d in self.doors:
            d.draw(surface, self.maze, visibility_radius, player_row, player_col)
        for k in self.keys:
            k.draw(surface, self.maze, visibility_radius, player_row, player_col)

    def try_unlock_door(self, row, col, game):
        """
        Checks if player holds key to open matching door.
        """
        door = self.doors_by_position.get((row, col))
        if door and door.is_locked:
            color = door.color
            if self.inventory.get(color, 0) > 0:
                self.inventory[color] -= 1
                door.is_locked = False

                # Recalculate path for Shadow Monster
                if game.shadow_monster:
                    game.shadow_monster.move_timer = 0.0

                if hasattr(game.hud, "show_notification"):
                    game.hud.show_notification("Door Unlocked!")
            else:
                if hasattr(game.hud, "show_notification"):
                    game.hud.show_notification("Door Locked. Find matching key.")
                game.player.play_wall_hit_animation()  # Shake player

    def collect_key(self, key, game):
        """
        Collects key, adds to inventory, and triggers visual sparkle burst.
        """
        key.collected = True
        self.inventory[key.color] = self.inventory.get(key.color, 0) + 1

        cx, cy = game.maze.get_cell_center(key.row, key.col)
        if hasattr(game.particle_manager, "create_key_burst"):
            game.particle_manager.create_key_burst(cx, cy, key.color)

        if hasattr(game.hud, "show_notification"):
            game.hud.show_notification(f"{key.color} Key Collected!")

    def spawn_doors_and_keys(self, game, count):
        """
        Attempts random layouts, validating solvable constraints.
        """
        self.reset()
        colors = ["Red", "Blue", "Green", "Gold"]
        game_colors = colors[:count]

        player_row, player_col = game.get_start_position()
        exit_row, exit_col = game.get_exit_position()

        # Try to locate valid path coords
        path_cells = []
        for r in range(1, self.maze.rows - 1):
            for c in range(1, self.maze.cols - 1):
                if game.maze_is_path(r, c):
                    path_cells.append((r, c))

        # Exclude player start area for door placements
        avoid_door_cells = {
            (player_row, player_col),
            (player_row - 1, player_col),
            (player_row + 1, player_col),
            (player_row, player_col - 1),
            (player_row, player_col + 1),
            (exit_row, exit_col)
        }

        # Exclude start, exit, traps, batteries, powerups for key placements
        avoid_key_cells = {
            (player_row, player_col),
            (exit_row, exit_col)
        }
        if game.shadow_monster:
            avoid_key_cells.add((game.shadow_monster.row, game.shadow_monster.col))
        if game.battery_manager and hasattr(game.battery_manager, "pickups"):
            for b in game.battery_manager.pickups:
                avoid_key_cells.add((b.row, b.col))
        if game.powerup_manager and hasattr(game.powerup_manager, "spawned_powerups"):
            for p in game.powerup_manager.spawned_powerups:
                avoid_key_cells.add((p.row, p.col))
        if game.trap_manager and hasattr(game.trap_manager, "traps"):
            for t in game.trap_manager.traps:
                avoid_key_cells.add((t.row, t.col))

        door_candidates = [c for c in path_cells if c not in avoid_door_cells]
        key_candidates = [c for c in path_cells if c not in avoid_key_cells]

        if len(door_candidates) < count or len(key_candidates) < count * 2:
            return False

        max_attempts = 800
        for _ in range(max_attempts):
            proposed_doors = {}
            proposed_keys = {}

            door_pos = random.sample(door_candidates, count)
            # Keys cannot overlay doors
            valid_keys = [c for c in key_candidates if c not in door_pos]
            if len(valid_keys) < count:
                continue
            key_pos = random.sample(valid_keys, count)

            for i, col in enumerate(game_colors):
                proposed_doors[door_pos[i]] = col
                proposed_keys[col] = key_pos[i]

            # Solvability validation
            if self.simulate_solvability(game, proposed_doors, proposed_keys, player_row, player_col, exit_row, exit_col):
                for pos, col in proposed_doors.items():
                    d = Door(pos[0], pos[1], col)
                    self.doors.append(d)
                    self.doors_by_position[pos] = d
                for col, pos in proposed_keys.items():
                    k = Key(pos[0], pos[1], col)
                    self.keys.append(k)
                    self.keys_by_position[pos] = k
                return True

        return False

    def simulate_solvability(self, game, proposed_doors, proposed_keys, start_row, start_col, exit_row, exit_col):
        """
        Verifies if player can reach the exit by stepping on paths and unlocking doors.
        """
        closed_doors = set(proposed_doors.keys())
        uncollected_keys = {col: pos for col, pos in proposed_keys.items()}
        collected_keys = set()

        while True:
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
                    if not game.maze_is_path(nr, nc):
                        continue
                    if (nr, nc) in closed_doors:
                        continue
                    visited.add((nr, nc))
                    queue.append((nr, nc))

            if (exit_row, exit_col) in visited:
                return True

            keys_gained = False
            for col, pos in list(uncollected_keys.items()):
                if pos in visited:
                    collected_keys.add(col)
                    del uncollected_keys[col]

                    # Unlock matching door in simulator
                    matching_door = None
                    for dp, dcol in proposed_doors.items():
                        if dcol == col:
                            matching_door = dp
                            break
                    if matching_door in closed_doors:
                        closed_doors.remove(matching_door)
                    keys_gained = True

            if not keys_gained:
                return False
