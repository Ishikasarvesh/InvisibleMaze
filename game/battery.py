import random

import pygame

from game.animations import floating_offset, pulse
from game.settings import (
    BATTERY_COLOR,
    BATTERY_FLOAT_SPEED,
    BATTERY_GLOW,
    YELLOW,
)


class BatteryPickup:
    """
    Represents one battery pickup inside the maze.
    """

    def __init__(
        self,
        row,
        col,
        restore_amount,
    ):
        self.row = row
        self.col = col

        self.restore_amount = restore_amount

        self.collected = False

        self.animation_time = random.uniform(
            0,
            10,
        )

    def get_position(self):
        """
        Returns the battery's maze position.
        """

        return (
            self.row,
            self.col,
        )

    def update(self, delta_time):
        """
        Updates floating and glow animations.
        """

        self.animation_time += delta_time

    def draw(
        self,
        surface,
        maze,
        visible,
    ):
        """
        Draws the battery only when it is visible.
        """

        if self.collected or not visible:
            return

        center_x, center_y = maze.get_cell_center(
            self.row,
            self.col,
        )

        float_y = floating_offset(
            self.animation_time,
            speed=BATTERY_FLOAT_SPEED,
            distance=max(
                2,
                maze.cell_size * 0.08,
            ),
        )

        center_y += int(float_y)

        glow_value = pulse(
            self.animation_time,
            speed=4,
            minimum=0.8,
            maximum=1.2,
        )

        body_width = max(
            8,
            int(maze.cell_size * 0.38),
        )

        body_height = max(
            12,
            int(maze.cell_size * 0.58),
        )

        glow_radius = int(
            maze.cell_size
            * 0.65
            * glow_value
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
            body_width,
            body_height,
        )

    def draw_glow(
        self,
        surface,
        center_x,
        center_y,
        radius,
    ):
        """
        Draws a soft transparent glow around the battery.
        """

        glow_surface = pygame.Surface(
            surface.get_size(),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            glow_surface,
            (
                BATTERY_GLOW[0],
                BATTERY_GLOW[1],
                BATTERY_GLOW[2],
                22,
            ),
            (
                center_x,
                center_y,
            ),
            radius,
        )

        pygame.draw.circle(
            glow_surface,
            (
                BATTERY_GLOW[0],
                BATTERY_GLOW[1],
                BATTERY_GLOW[2],
                48,
            ),
            (
                center_x,
                center_y,
            ),
            max(
                5,
                radius // 2,
            ),
        )

        surface.blit(
            glow_surface,
            (0, 0),
        )

    def draw_battery_body(
        self,
        surface,
        center_x,
        center_y,
        width,
        height,
    ):
        """
        Draws the battery body and energy symbol.
        """

        body_rect = pygame.Rect(
            center_x - width // 2,
            center_y - height // 2,
            width,
            height,
        )

        pygame.draw.rect(
            surface,
            BATTERY_COLOR,
            body_rect,
            border_radius=max(
                2,
                width // 5,
            ),
        )

        pygame.draw.rect(
            surface,
            YELLOW,
            body_rect,
            width=max(
                1,
                width // 8,
            ),
            border_radius=max(
                2,
                width // 5,
            ),
        )

        terminal_width = max(
            3,
            width // 2,
        )

        terminal_height = max(
            2,
            height // 8,
        )

        terminal_rect = pygame.Rect(
            center_x - terminal_width // 2,
            body_rect.top - terminal_height + 1,
            terminal_width,
            terminal_height,
        )

        pygame.draw.rect(
            surface,
            BATTERY_GLOW,
            terminal_rect,
            border_radius=2,
        )

        bolt_points = [
            (
                center_x + 1,
                center_y - height // 4,
            ),
            (
                center_x - width // 5,
                center_y,
            ),
            (
                center_x,
                center_y,
            ),
            (
                center_x - 1,
                center_y + height // 4,
            ),
            (
                center_x + width // 5,
                center_y,
            ),
            (
                center_x,
                center_y,
            ),
        ]

        pygame.draw.polygon(
            surface,
            (90, 65, 20),
            bolt_points,
        )


class BatteryManager:
    """
    Generates, updates and manages battery pickups.
    """

    def __init__(
        self,
        maze,
        pickup_count,
        restore_amount,
    ):
        self.maze = maze

        self.pickup_count = pickup_count
        self.restore_amount = restore_amount

        self.pickups = []

        self.generate_pickups()

    def generate_pickups(self):
        """
        Randomly places battery pickups on valid path cells.
        """

        possible_positions = []

        for row in range(
            1,
            self.maze.rows - 1,
        ):
            for col in range(
                1,
                self.maze.cols - 1,
            ):
                if not self.maze.is_path(
                    row,
                    col,
                ):
                    continue

                position = (
                    row,
                    col,
                )

                if position == self.maze.start_position:
                    continue

                if position == self.maze.exit_position:
                    continue

                possible_positions.append(
                    position
                )

        number_to_generate = min(
            self.pickup_count,
            len(possible_positions),
        )

        selected_positions = random.sample(
            possible_positions,
            number_to_generate,
        )

        self.pickups = [
            BatteryPickup(
                row,
                col,
                self.restore_amount,
            )
            for row, col in selected_positions
        ]

    def update(self, delta_time):
        """
        Updates each active pickup.
        """

        for pickup in self.pickups:
            pickup.update(delta_time)

    def draw(
        self,
        surface,
        player_row,
        player_col,
        visibility_radius,
    ):
        """
        Draws visible pickups.
        """

        for pickup in self.pickups:
            visible = self.maze.is_cell_visible(
                pickup.row,
                pickup.col,
                player_row,
                player_col,
                visibility_radius,
            )

            pickup.draw(
                surface,
                self.maze,
                visible,
            )

    def collect_at(
        self,
        row,
        col,
    ):
        """
        Collects a battery at the player's position.

        Returns the restored battery amount.
        Returns 0 when there is no pickup.
        """

        for pickup in self.pickups:
            if pickup.collected:
                continue

            if (
                pickup.row == row
                and pickup.col == col
            ):
                pickup.collected = True

                return pickup.restore_amount

        return 0

    def get_remaining_count(self):
        """
        Returns the number of uncollected batteries.
        """

        return sum(
            1
            for pickup in self.pickups
            if not pickup.collected
        )

    def reset(self):
        """
        Generates a fresh set of pickups.
        """

        self.generate_pickups()