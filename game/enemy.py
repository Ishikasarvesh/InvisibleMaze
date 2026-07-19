from collections import deque
import math
import random

import pygame


class ShadowMonster:
    """
    Shadow monster that follows the player through valid maze paths.
    """

    def __init__(
        self,
        maze,
        start_row,
        start_col,
        move_interval=1.0,
        damage=15,
    ):
        self.maze = maze

        self.row = start_row
        self.col = start_col

        self.target_row = start_row
        self.target_col = start_col

        self.move_interval = float(move_interval)
        self.move_timer = float(move_interval)

        self.damage = float(damage)

        self.is_moving = False
        self.move_progress = 0.0
        self.move_duration = 0.20

        start_x, start_y = self.maze.get_cell_center(
            self.row,
            self.col,
        )

        self.x = float(start_x)
        self.y = float(start_y)

        self.start_x = float(start_x)
        self.start_y = float(start_y)

        self.target_x = float(start_x)
        self.target_y = float(start_y)

        self.animation_time = 0.0
        self.alarm_active = False

    def update(
        self,
        delta_time,
        player_row,
        player_col,
        battery_percentage,
    ):
        self.animation_time += delta_time

        if self.is_moving:
            self.update_movement(delta_time)
            return

        self.move_timer -= delta_time

        if self.move_timer > 0:
            return

        speed_multiplier = 1.0

        if battery_percentage < 25:
            speed_multiplier = 1.45

        alarm_multiplier = 1.60 if getattr(self, "alarm_active", False) else 1.0

        self.move_timer = max(
            0.15,
            self.move_interval / (speed_multiplier * alarm_multiplier),
        )

        next_position = self.find_next_step(
            player_row,
            player_col,
        )

        if next_position is None:
            return

        next_row, next_col = next_position

        self.begin_move(
            next_row,
            next_col,
        )

    def begin_move(
        self,
        next_row,
        next_col,
    ):
        self.start_x = self.x
        self.start_y = self.y

        self.target_row = next_row
        self.target_col = next_col

        target_x, target_y = self.maze.get_cell_center(
            next_row,
            next_col,
        )

        self.target_x = float(target_x)
        self.target_y = float(target_y)

        self.move_progress = 0.0
        self.is_moving = True

    def update_movement(
        self,
        delta_time,
    ):
        self.move_progress += (
            delta_time / self.move_duration
        )

        progress = min(
            1.0,
            self.move_progress,
        )

        smooth_progress = (
            progress
            * progress
            * (3 - 2 * progress)
        )

        self.x = (
            self.start_x
            + (
                self.target_x
                - self.start_x
            )
            * smooth_progress
        )

        self.y = (
            self.start_y
            + (
                self.target_y
                - self.start_y
            )
            * smooth_progress
        )

        if progress >= 1.0:
            self.row = self.target_row
            self.col = self.target_col

            self.x = self.target_x
            self.y = self.target_y

            self.is_moving = False

    def find_next_step(
        self,
        player_row,
        player_col,
    ):
        """
        Uses breadth-first search to find the shortest path.
        """

        start = (
            self.row,
            self.col,
        )

        target = (
            player_row,
            player_col,
        )

        if start == target:
            return None

        queue = deque([start])
        visited = {start}
        previous = {start: None}

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]

        random.shuffle(directions)

        found_target = False

        while queue:
            current = queue.popleft()

            if current == target:
                found_target = True
                break

            current_row, current_col = current

            for row_change, col_change in directions:
                next_row = (
                    current_row
                    + row_change
                )

                next_col = (
                    current_col
                    + col_change
                )

                next_position = (
                    next_row,
                    next_col,
                )

                if next_position in visited:
                    continue

                if not self.is_walkable(
                    next_row,
                    next_col,
                ):
                    continue

                visited.add(next_position)

                previous[next_position] = (
                    current
                )

                queue.append(next_position)

        if not found_target:
            return self.get_random_step()

        current = target

        while (
            previous.get(current) is not None
            and previous[current] != start
        ):
            current = previous[current]

        if previous.get(current) == start:
            return current

        return None

    def get_random_step(self):
        valid_positions = []

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]

        for row_change, col_change in directions:
            next_row = (
                self.row
                + row_change
            )

            next_col = (
                self.col
                + col_change
            )

            if self.is_walkable(
                next_row,
                next_col,
            ):
                valid_positions.append(
                    (
                        next_row,
                        next_col,
                    )
                )

        if not valid_positions:
            return None

        return random.choice(
            valid_positions
        )

    def is_walkable(
        self,
        row,
        col,
    ):
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

            except (IndexError, TypeError):
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

            value = self.maze.grid[row][col]

            return value != 1

        return False

    def distance_to_player(
        self,
        player_row,
        player_col,
    ):
        return (
            abs(self.row - player_row)
            + abs(self.col - player_col)
        )

    def is_touching_player(
        self,
        player_row,
        player_col,
    ):
        return (
            not self.is_moving
            and self.row == player_row
            and self.col == player_col
        )

    def draw(
        self,
        surface,
        player_row,
        player_col,
        visibility_radius,
    ):
        distance = (
            abs(self.row - player_row)
            + abs(self.col - player_col)
        )

        if distance > visibility_radius:
            return

        pulse = (
            math.sin(
                self.animation_time * 7
            )
            + 1
        ) / 2

        body_radius = max(
            8,
            int(
                self.maze.cell_size
                * (
                    0.28
                    + pulse * 0.04
                )
            ),
        )

        center = (
            int(self.x),
            int(self.y),
        )

        shadow_surface = pygame.Surface(
            surface.get_size(),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            shadow_surface,
            (
                90,
                0,
                110,
                24,
            ),
            center,
            body_radius + 20,
        )

        pygame.draw.circle(
            shadow_surface,
            (
                45,
                0,
                60,
                45,
            ),
            center,
            body_radius + 10,
        )

        pygame.draw.circle(
            shadow_surface,
            (
                8,
                4,
                15,
                205,
            ),
            center,
            body_radius,
        )

        surface.blit(
            shadow_surface,
            (0, 0),
        )

        eye_offset_x = max(
            3,
            body_radius // 3,
        )

        eye_offset_y = max(
            2,
            body_radius // 5,
        )

        eye_radius = max(
            2,
            body_radius // 7,
        )

        pygame.draw.circle(
            surface,
            (
                255,
                35,
                45,
            ),
            (
                center[0] - eye_offset_x,
                center[1] - eye_offset_y,
            ),
            eye_radius,
        )

        pygame.draw.circle(
            surface,
            (
                255,
                35,
                45,
            ),
            (
                center[0] + eye_offset_x,
                center[1] - eye_offset_y,
            ),
            eye_radius,
        )