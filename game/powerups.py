import math
import random
import sys
import pygame

class PowerUp:
    """
    Represents a mystery power-up collectible box in the maze.
    """

    def __init__(self, row, col, type_name, cell_size, start_x, start_y):
        self.row = row
        self.col = col
        self.type = type_name
        self.cell_size = cell_size

        # Compute screen position at the center of the cell
        self.x = float(start_x + col * cell_size + cell_size / 2)
        self.y = float(start_y + row * cell_size + cell_size / 2)

        self.animation_time = random.uniform(0.0, 100.0)
        self.collected = False

    def update(self, delta_time, game):
        """
        Updates floating and idle particle animations.
        """
        self.animation_time += delta_time

        # Spawn idle sparkle particles around the box
        if random.random() < 0.10:
            if hasattr(game.particle_manager, "create_sparkle"):
                float_y = self.y + self.get_float_offset()
                game.particle_manager.create_sparkle(self.x, float_y)

    def get_float_offset(self):
        """
        Generates vertical offset for floating animation.
        """
        return math.sin(self.animation_time * 5.0) * 3.5

    def draw(self, surface, fonts):
        """
        Draws the mystery box with a soft golden glow, pulsing box, and "?" mark.
        """
        if self.collected:
            return

        float_y = self.y + self.get_float_offset()
        size = self.cell_size * 0.50

        # 1. Soft Glow (Translucent Golden Circle)
        glow_radius = int(size * 1.5)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pulse_val = (math.sin(self.animation_time * 4.0) + 1.0) / 2.0
        glow_alpha = int(25 + pulse_val * 20)  # Pulse alpha between 25 and 45
        
        pygame.draw.circle(
            glow_surface,
            (255, 215, 0, glow_alpha),
            (glow_radius, glow_radius),
            glow_radius
        )
        surface.blit(glow_surface, (int(self.x - glow_radius), int(float_y - glow_radius)))

        # 2. Pulsing Golden Outline Box
        box_rect = pygame.Rect(self.x - size / 2, float_y - size / 2, size, size)
        
        # Draw background inside mystery box
        pygame.draw.rect(surface, (18, 22, 34), box_rect, border_radius=4)
        # Gold outline
        pygame.draw.rect(surface, (255, 207, 70), box_rect, width=2, border_radius=4)

        # 3. Pulsing "?" in the center
        text_surf = fonts["body"].render("?", True, (255, 221, 116))
        
        # Scale/fade the text slightly to pulse
        text_alpha = int(180 + pulse_val * 75)
        text_surf.set_alpha(text_alpha)
        
        text_rect = text_surf.get_rect(center=(self.x, float_y))
        surface.blit(text_surf, text_rect)


class PowerUpManager:
    """
    Manages spawning, collisions, updates, and activations of power-ups.
    """

    def __init__(self, maze, fonts):
        self.maze = maze
        self.fonts = fonts
        self.spawned_powerups = []
        self.active_powerups = {}  # Active durations: {type_name: remaining_seconds}

        self.original_player_speed = 12.0
        self.original_is_path = None

        # Registry of effects for future expandability
        self.effects = {
            "Torch": {
                "name": "Super Torch",
                "icon": "🔦",
                "duration": 10.0,
                "activate": self.activate_torch,
                "deactivate": self.deactivate_torch,
            },
            "Battery": {
                "name": "Battery Boost",
                "icon": "🔋",
                "duration": 0.0,  # Instant
                "activate": self.activate_battery,
            },
            "Freeze": {
                "name": "Freeze",
                "icon": "❄️",
                "duration": 8.0,
                "activate": self.activate_freeze,
                "deactivate": self.deactivate_freeze,
            },
            "Speed": {
                "name": "Speed Boost",
                "icon": "⚡",
                "duration": 10.0,
                "activate": self.activate_speed,
                "deactivate": self.deactivate_speed,
            },
            "Ghost": {
                "name": "Ghost Mode",
                "icon": "👻",
                "duration": 5.0,
                "activate": self.activate_ghost,
                "deactivate": self.deactivate_ghost,
            },
            "Time": {
                "name": "Time Bonus",
                "icon": "⏳",
                "duration": 0.0,  # Instant
                "activate": self.activate_time,
            },
            "Score": {
                "name": "Score Bonus",
                "icon": "💎",
                "duration": 0.0,  # Instant
                "activate": self.activate_score,
            },
            "Teleport": {
                "name": "Monster Teleport",
                "icon": "🌀",
                "duration": 0.0,  # Instant
                "activate": self.activate_teleport,
            }
        }

    def reset_effects(self, game):
        """
        Deactivates all power-up effects and restores original values.
        """
        self.active_powerups.clear()

        # Restore Player Speed
        if game.player:
            import game.player
            game.player.PLAYER_MOVE_SPEED = self.original_player_speed

        # Restore Ghost collision
        if self.original_is_path is not None and game.maze:
            game.maze.is_path = self.original_is_path
            self.original_is_path = None

    def is_active(self, type_name):
        """
        Checks if a power-up type is currently active.
        """
        return self.active_powerups.get(type_name, 0.0) > 0.0

    def spawn_powerups(self, game, count):
        """
        Spawns random mystery boxes throughout the maze.
        """
        self.spawned_powerups.clear()
        self.reset_effects(game)

        # Get positions to avoid
        player_row, player_col = game.get_start_position()
        exit_row, exit_col = game.get_exit_position()

        monster_row, monster_col = -1, -1
        if game.shadow_monster:
            monster_row = game.shadow_monster.row
            monster_col = game.shadow_monster.col

        battery_positions = set()
        if game.battery_manager and hasattr(game.battery_manager, "pickups"):
            for b in game.battery_manager.pickups:
                battery_positions.add((b.row, b.col))

        possible_positions = []
        for r in range(1, self.maze.rows - 1):
            for c in range(1, self.maze.cols - 1):
                # Cannot spawn in walls
                if not game.maze_is_path(r, c):
                    continue
                # Cannot spawn on player
                if r == player_row and c == player_col:
                    continue
                # Cannot spawn on exit
                if r == exit_row and c == exit_col:
                    continue
                # Cannot spawn on battery pickups
                if (r, c) in battery_positions:
                    continue
                # Cannot spawn on monster
                if r == monster_row and c == monster_col:
                    continue

                possible_positions.append((r, c))

        if not possible_positions:
            return

        spawn_count = min(count, len(possible_positions))
        selected_positions = random.sample(possible_positions, spawn_count)

        powerup_types = list(self.effects.keys())

        for r, c in selected_positions:
            ptype = random.choice(powerup_types)
            p = PowerUp(
                row=r,
                col=c,
                type_name=ptype,
                cell_size=self.maze.cell_size,
                start_x=self.maze.start_x,
                start_y=self.maze.start_y
            )
            self.spawned_powerups.append(p)

    def check_collisions(self, game):
        """
        Checks if the player collects a mystery box.
        """
        if not game.player:
            return

        player_row = game.player.row
        player_col = game.player.col

        for p in self.spawned_powerups:
            if not p.collected and p.row == player_row and p.col == player_col:
                p.collected = True
                self.activate_powerup(p.type, game, p.x, p.y)

    def activate_powerup(self, type_name, game, x, y):
        """
        Triggers collection effects and calls the activation method of the power-up.
        """
        config = self.effects.get(type_name)
        if not config:
            return

        # 1. Golden particle burst
        if hasattr(game.particle_manager, "create_powerup_burst"):
            game.particle_manager.create_powerup_burst(x, y)

        # 2. Screen Flash trigger
        game.screen_flash = 0.20

        # 3. Sound hook placeholder
        # print(f"[Sound Hook] Play power-up collection sound for {type_name}")

        # 4. Notify player
        if hasattr(game.hud, "show_notification"):
            game.hud.show_notification(f"{config['name']} Activated!")

        # 5. Activate effect
        duration = config["duration"]
        if duration > 0.0:
            self.active_powerups[type_name] = duration
        
        config["activate"](game)

    def update(self, delta_time, game):
        """
        Updates spawned power-ups and counts down active power-up timers.
        """
        # Update boxes floating and sparkles
        for p in self.spawned_powerups:
            if not p.collected:
                p.update(delta_time, game)

        # Count down durations
        expired = []
        for k in list(self.active_powerups.keys()):
            self.active_powerups[k] -= delta_time
            if self.active_powerups[k] <= 0:
                expired.append(k)

        # Deactivate expired ones
        for k in expired:
            del self.active_powerups[k]
            deactivate_method = self.effects[k].get("deactivate")
            if deactivate_method:
                deactivate_method(game)

    def draw(self, surface):
        """
        Draws all active mystery box items.
        """
        for p in self.spawned_powerups:
            p.draw(surface, self.fonts)

    # =====================================================
    # SPECIFIC POWER-UP EFFECT METHODS
    # =====================================================

    def activate_torch(self, game):
        # Simply sets the timer, game.py get_visibility_radius handles the offset
        pass

    def deactivate_torch(self, game):
        pass

    def activate_battery(self, game):
        # Restore +35% battery
        game.battery_percentage = min(game.maximum_battery, game.battery_percentage + 35.0)

    def activate_freeze(self, game):
        # Bypasses monster update in game.py while active
        pass

    def deactivate_freeze(self, game):
        pass

    def activate_speed(self, game):
        # Increase speed by 40%
        if game.player:
            import game.player
            game.player.PLAYER_MOVE_SPEED = self.original_player_speed * 1.40

    def deactivate_speed(self, game):
        # Restore original speed
        if game.player:
            import game.player
            game.player.PLAYER_MOVE_SPEED = self.original_player_speed

    def activate_ghost(self, game):
        # Pass through walls: override maze is_path method
        if game.maze:
            if self.original_is_path is None:
                self.original_is_path = game.maze.is_path
            game.maze.is_path = lambda r, c: game.maze.is_inside(r, c)

    def deactivate_ghost(self, game):
        # Re-enable collision
        if game.maze and self.original_is_path is not None:
            game.maze.is_path = self.original_is_path
            self.original_is_path = None

    def activate_time(self, game):
        # Subtract 20 seconds from timer
        game.game_start_time += 20.0

    def activate_score(self, game):
        # Add 500 score (handled dynamically in game.py update_score)
        game.powerup_score_bonus = getattr(game, "powerup_score_bonus", 0) + 500

    def activate_teleport(self, game):
        # Teleport monster far away
        if game.shadow_monster:
            new_row, new_col = game.find_monster_start_position(game.player.row, game.player.col)
            game.shadow_monster.row = new_row
            game.shadow_monster.col = new_col

            cx, cy = game.maze.get_cell_center(new_row, new_col)
            game.shadow_monster.x = float(cx)
            game.shadow_monster.y = float(cy)
            game.shadow_monster.target_row = new_row
            game.shadow_monster.target_col = new_col
            game.shadow_monster.target_x = float(cx)
            game.shadow_monster.target_y = float(cy)
            game.shadow_monster.is_moving = False
