import math
import random
import pygame

from game.animations import (
    pulse,
)
from game.settings import (
    BATTERY_COLOR,
    BATTERY_FLOAT_SPEED,
    BATTERY_GLOW,
    WHITE,
    YELLOW,
)


class BatteryPickup:
    """
    A battery item placed inside the maze.
    Collecting it restores torch power.
    """

    def __init__(
        self,
        row,
        col,
        restore_amount=25,
    ):
        self.row = row
        self.col = col

        self.restore_amount = restore_amount

        self.collected = False

        self.animation_offset = random.uniform(
            0,
            math.pi * 2,
        )

    # =====================================================
    # DRAWING
    # =====================================================

    def draw(
        self,
        surface,
        maze,
        animation_time,
    ):
        """
        Draws the battery inside the cell.
        """
        if self.collected:
            return

        center_x, center_y = (
            maze.get_cell_center(
                self.row,
                self.col,
            )
        )

        float_y = (
            math.sin(
                animation_time
                * BATTERY_FLOAT_SPEED
                + self.animation_offset
            )
            * 3
        )

        center_y += int(float_y)

        glow_pulse = pulse(
            animation_time
            + self.animation_offset,
            speed=3,
            minimum=0.88,
            maximum=1.12,
        )

        glow_radius = int(
            maze.cell_size
            * 0.28
            * glow_pulse
        )

        self.draw_glow(
            surface,
            center_x,
            center_y,
            glow_radius,
        )

        self.draw_battery_body(
            surface,
            center_x,
            center_y,
            maze.cell_size,
        )

    def draw_glow(
        self,
        surface,
        center_x,
        center_y,
        radius,
    ):
        """
        Draws a small soft transparent glow around the battery.
        """
        r_int = max(4, radius)
        glow_size = r_int * 2
        glow_surface = pygame.Surface(
            (glow_size, glow_size),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            glow_surface,
            (
                BATTERY_GLOW[0],
                BATTERY_GLOW[1],
                BATTERY_GLOW[2],
                28,
            ),
            (r_int, r_int),
            r_int,
        )

        surface.blit(
            glow_surface,
            (center_x - r_int, center_y - r_int),
        )

    def draw_battery_body(
        self,
        surface,
        center_x,
        center_y,
        cell_size,
    ):
        """
        Draws the battery sprite.
        """
        width = max(
            8,
            int(cell_size * 0.28),
        )

        height = max(
            12,
            int(cell_size * 0.44),
        )

        body_rect = pygame.Rect(
            center_x - width // 2,
            center_y - height // 2,
            width,
            height,
        )

        pygame.draw.rect(
            surface,
            (
                28,
                34,
                48,
            ),
            body_rect,
            border_radius=4,
        )

        pygame.draw.rect(
            surface,
            BATTERY_COLOR,
            body_rect,
            width=2,
            border_radius=4,
        )

        cap_width = max(
            4,
            width // 2,
        )

        cap_height = max(
            2,
            height // 6,
        )

        cap_rect = pygame.Rect(
            center_x - cap_width // 2,
            body_rect.top - cap_height,
            cap_width,
            cap_height,
        )

        pygame.draw.rect(
            surface,
            BATTERY_COLOR,
            cap_rect,
            border_radius=1,
        )

        fill_height = max(
            2,
            int(body_rect.height * 0.65),
        )

        fill_rect = pygame.Rect(
            body_rect.left + 2,
            body_rect.bottom
            - fill_height
            - 2,
            body_rect.width - 4,
            fill_height,
        )

        pygame.draw.rect(
            surface,
            BATTERY_COLOR,
            fill_rect,
            border_radius=2,
        )


class BatteryManager:
    """
    Spawns and manages battery pickups.
    """

    def __init__(self, maze, *args, **kwargs):
        self.maze = maze
        self.pickups = []
        self.animation_time = 0

    def update(self, delta_time):
        self.animation_time += delta_time

    def spawn_pickups(self, count, avoid_cells=None):
        self.pickups.clear()

        valid_positions = []
        for r in range(1, self.maze.rows - 1):
            for c in range(1, self.maze.cols - 1):
                if self.maze.is_path(r, c):
                    if avoid_cells and (r, c) in avoid_cells:
                        continue
                    valid_positions.append((r, c))

        if not valid_positions:
            return

        spawn_count = min(count, len(valid_positions))
        selected = random.sample(valid_positions, spawn_count)

        for r, c in selected:
            self.pickups.append(BatteryPickup(r, c))

    def draw(self, surface, player_row, player_col, visibility_radius):
        for p in self.pickups:
            dist = abs(p.row - player_row) + abs(p.col - player_col)
            if dist <= visibility_radius:
                p.draw(surface, self.maze, self.animation_time)