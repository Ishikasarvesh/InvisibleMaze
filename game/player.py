import math

import pygame

from game.animations import (
    AnimatedValue,
    approach,
    pulse,
)
from game.settings import (
    PLAYER_COLOR,
    PLAYER_HIGHLIGHT,
    PLAYER_MOVE_SPEED,
    PLAYER_PULSE_SPEED,
)


class Player:
    """
    Controls player movement, position and animation.
    """

    def __init__(
        self,
        maze,
        start_row=1,
        start_col=1,
    ):
        self.maze = maze

        self.row = start_row
        self.col = start_col

        start_x, start_y = (
            self.maze.get_cell_center(
                self.row,
                self.col,
            )
        )

        # Actual rendered position.
        self.x = float(start_x)
        self.y = float(start_y)

        # Position the player moves toward.
        self.target_x = float(start_x)
        self.target_y = float(start_y)

        self.moves = 0

        self.animation_time = 0

        self.hit_animation = AnimatedValue(0)

        self.last_move_direction = (0, 0)

        self.is_moving = False

    # =====================================================
    # POSITION
    # =====================================================

    def reset(
        self,
        row=1,
        col=1,
    ):
        """
        Returns the player to a starting cell.
        """

        self.row = row
        self.col = col

        center_x, center_y = (
            self.maze.get_cell_center(
                row,
                col,
            )
        )

        self.x = float(center_x)
        self.y = float(center_y)

        self.target_x = float(center_x)
        self.target_y = float(center_y)

        self.moves = 0
        self.last_move_direction = (0, 0)

        self.hit_animation.snap(0)

        self.maze.mark_visited(
            row,
            col,
        )

    def get_grid_position(self):
        """
        Returns the maze row and column.
        """

        return (
            self.row,
            self.col,
        )

    def get_screen_position(self):
        """
        Returns the animated screen position.
        """

        return (
            int(self.x),
            int(self.y),
        )

    # =====================================================
    # MOVEMENT
    # =====================================================

    def try_move(
        self,
        row_change,
        col_change,
    ):
        """
        Attempts to move the player.

        Returns True when movement succeeds.
        Returns False when the player hits a wall.
        """

        if self.is_moving:
            return False

        new_row = self.row + row_change
        new_col = self.col + col_change

        self.last_move_direction = (
            row_change,
            col_change,
        )

        if not self.maze.is_path(
            new_row,
            new_col,
        ):
            self.play_wall_hit_animation()

            return False

        self.row = new_row
        self.col = new_col

        self.moves += 1

        self.maze.mark_visited(
            self.row,
            self.col,
        )

        self.target_x, self.target_y = (
            self.maze.get_cell_center(
                self.row,
                self.col,
            )
        )

        self.is_moving = True

        return True

    def move_up(self):
        return self.try_move(-1, 0)

    def move_down(self):
        return self.try_move(1, 0)

    def move_left(self):
        return self.try_move(0, -1)

    def move_right(self):
        return self.try_move(0, 1)

    # =====================================================
    # WALL-HIT ANIMATION
    # =====================================================

    def play_wall_hit_animation(self):
        """
        Starts a small shake when the player hits a wall.
        """

        self.hit_animation.snap(1)
        self.hit_animation.set_target(0)

    def get_wall_hit_offset(self):
        """
        Creates a brief movement in the attempted direction.
        """

        strength = self.hit_animation.value * 5

        row_direction, col_direction = (
            self.last_move_direction
        )

        offset_x = (
            col_direction * strength
        )

        offset_y = (
            row_direction * strength
        )

        return (
            offset_x,
            offset_y,
        )

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, delta_time):
        """
        Updates movement and animations.
        """

        self.animation_time += delta_time

        self.hit_animation.update(
            delta_time,
            speed=18,
        )

        self.x = approach(
            self.x,
            self.target_x,
            PLAYER_MOVE_SPEED,
            delta_time,
        )

        self.y = approach(
            self.y,
            self.target_y,
            PLAYER_MOVE_SPEED,
            delta_time,
        )

        distance_x = abs(
            self.target_x - self.x
        )

        distance_y = abs(
            self.target_y - self.y
        )

        if (
            distance_x < 0.5
            and distance_y < 0.5
        ):
            self.x = self.target_x
            self.y = self.target_y

            self.is_moving = False

    # =====================================================
    # DRAWING
    # =====================================================

    def draw(
        self,
        surface,
        visibility_radius,
        battery_percentage,
    ):
        """
        Draws the player and torch glow.
        """

        player_x, player_y = (
            self.get_screen_position()
        )

        hit_offset_x, hit_offset_y = (
            self.get_wall_hit_offset()
        )

        player_x += int(hit_offset_x)
        player_y += int(hit_offset_y)

        glow_pulse = pulse(
            self.animation_time,
            speed=PLAYER_PULSE_SPEED,
            minimum=0.92,
            maximum=1.08,
        )

        battery_strength = max(
            0.2,
            battery_percentage / 100,
        )

        glow_radius = int(
            self.maze.cell_size
            * (visibility_radius + 0.7)
            * glow_pulse
            * (
                0.75
                + battery_strength * 0.25
            )
        )

        self.draw_torch_glow(
            surface,
            player_x,
            player_y,
            glow_radius,
            battery_percentage,
        )

        player_radius = max(
            5,
            int(
                self.maze.cell_size
                * 0.27
                * glow_pulse
            ),
        )

        pygame.draw.circle(
            surface,
            PLAYER_COLOR,
            (player_x, player_y),
            player_radius,
        )

        highlight_radius = max(
            2,
            player_radius // 4,
        )

        pygame.draw.circle(
            surface,
            PLAYER_HIGHLIGHT,
            (
                player_x
                - player_radius // 3,
                player_y
                - player_radius // 3,
            ),
            highlight_radius,
        )

        self.draw_player_face(
            surface,
            player_x,
            player_y,
            player_radius,
        )

    def draw_torch_glow(
        self,
        surface,
        center_x,
        center_y,
        glow_radius,
        battery_percentage,
    ):
        """
        Draws transparent light circles around the player.
        """

        glow_surface = pygame.Surface(
            surface.get_size(),
            pygame.SRCALPHA,
        )

        battery_alpha = int(
            max(
                10,
                35 * battery_percentage / 100,
            )
        )

        pygame.draw.circle(
            glow_surface,
            (
                255,
                213,
                100,
                battery_alpha // 2,
            ),
            (center_x, center_y),
            glow_radius,
        )

        pygame.draw.circle(
            glow_surface,
            (
                255,
                224,
                130,
                battery_alpha,
            ),
            (center_x, center_y),
            max(
                10,
                glow_radius // 2,
            ),
        )

        pygame.draw.circle(
            glow_surface,
            (
                255,
                239,
                180,
                min(
                    80,
                    battery_alpha * 2,
                ),
            ),
            (center_x, center_y),
            max(
                6,
                glow_radius // 4,
            ),
        )

        surface.blit(
            glow_surface,
            (0, 0),
        )

    def draw_player_face(
        self,
        surface,
        center_x,
        center_y,
        radius,
    ):
        """
        Adds a small face to make the player
        feel more alive and friendly.
        """

        if radius < 7:
            return

        eye_radius = max(
            1,
            radius // 7,
        )

        eye_y = center_y - radius // 6

        eye_spacing = max(
            2,
            radius // 3,
        )

        pygame.draw.circle(
            surface,
            (45, 38, 30),
            (
                center_x - eye_spacing,
                eye_y,
            ),
            eye_radius,
        )

        pygame.draw.circle(
            surface,
            (45, 38, 30),
            (
                center_x + eye_spacing,
                eye_y,
            ),
            eye_radius,
        )

        mouth_rect = pygame.Rect(
            center_x - radius // 3,
            center_y,
            radius * 2 // 3,
            radius // 2,
        )

        pygame.draw.arc(
            surface,
            (70, 50, 35),
            mouth_rect,
            0,
            math.pi,
            width=max(
                1,
                radius // 8,
            ),
        )