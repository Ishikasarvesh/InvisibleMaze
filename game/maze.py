import random

import pygame

from game.settings import (
    HIDDEN_COLOR,
    PATH_COLOR,
    PATH_EDGE,
    VISITED_COLOR,
    WALL_COLOR,
    WALL_EDGE,
)


class Maze:
    """
    Generates, stores and draws the maze.

    Maze values:
    1 = wall
    0 = open path
    """

    def __init__(
        self,
        rows,
        cols,
        cell_size,
        start_x,
        start_y,
    ):
        self.rows = rows
        self.cols = cols

        self.cell_size = cell_size

        self.start_x = start_x
        self.start_y = start_y

        self.grid = []

        self.start_position = (1, 1)
        self.exit_position = (
            self.rows - 2,
            self.cols - 2,
        )

        self.visited_cells = set()

        self.generate()

    # =====================================================
    # MAZE GENERATION
    # =====================================================

    def create_wall_grid(self):
        """
        Creates a two-dimensional list filled with walls.
        """

        return [
            [1 for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

    def get_unvisited_neighbors(
        self,
        row,
        col,
    ):
        """
        Finds unvisited cells that are two spaces away.

        We move two cells because the cell between them
        acts as a removable wall.
        """

        directions = [
            (-2, 0),  # Up
            (2, 0),   # Down
            (0, -2),  # Left
            (0, 2),   # Right
        ]

        neighbors = []

        for row_change, col_change in directions:
            new_row = row + row_change
            new_col = col + col_change

            inside_maze = (
                1 <= new_row < self.rows - 1
                and 1 <= new_col < self.cols - 1
            )

            if not inside_maze:
                continue

            is_unvisited = (
                self.grid[new_row][new_col] == 1
            )

            if is_unvisited:
                neighbors.append(
                    (new_row, new_col)
                )

        return neighbors

    def generate(self):
        """
        Generates a random perfect maze using
        recursive backtracking.
        """

        self.grid = self.create_wall_grid()

        start_row, start_col = self.start_position

        self.grid[start_row][start_col] = 0

        stack = [
            (start_row, start_col)
        ]

        while stack:
            current_row, current_col = stack[-1]

            neighbors = self.get_unvisited_neighbors(
                current_row,
                current_col,
            )

            if neighbors:
                next_row, next_col = random.choice(
                    neighbors
                )

                wall_row = (
                    current_row + next_row
                ) // 2

                wall_col = (
                    current_col + next_col
                ) // 2

                # Remove the wall between the cells.
                self.grid[wall_row][wall_col] = 0

                # Mark the next cell as an open path.
                self.grid[next_row][next_col] = 0

                stack.append(
                    (next_row, next_col)
                )

            else:
                stack.pop()

        exit_row, exit_col = self.exit_position

        self.grid[exit_row][exit_col] = 0

        self.visited_cells = {
            self.start_position
        }

    # =====================================================
    # CELL INFORMATION
    # =====================================================

    def is_inside(self, row, col):
        """
        Checks whether a cell exists inside the maze.
        """

        return (
            0 <= row < self.rows
            and 0 <= col < self.cols
        )

    def is_path(self, row, col):
        """
        Returns True if the given cell is an open path.
        """

        if not self.is_inside(row, col):
            return False

        return self.grid[row][col] == 0

    def is_wall(self, row, col):
        """
        Returns True if the given cell is a wall.
        """

        if not self.is_inside(row, col):
            return True

        return self.grid[row][col] == 1

    def mark_visited(self, row, col):
        """
        Stores a cell as visited.
        """

        self.visited_cells.add(
            (row, col)
        )

    def was_visited(self, row, col):
        """
        Checks whether the player visited a cell.
        """

        return (
            row,
            col,
        ) in self.visited_cells

    # =====================================================
    # SCREEN POSITION HELPERS
    # =====================================================

    def get_cell_rect(self, row, col):
        """
        Converts a maze row and column into
        a Pygame rectangle.
        """

        x = (
            self.start_x
            + col * self.cell_size
        )

        y = (
            self.start_y
            + row * self.cell_size
        )

        return pygame.Rect(
            x,
            y,
            self.cell_size,
            self.cell_size,
        )

    def get_cell_center(self, row, col):
        """
        Returns the screen center of a maze cell.
        """

        rectangle = self.get_cell_rect(
            row,
            col,
        )

        return rectangle.center

    # =====================================================
    # VISIBILITY
    # =====================================================

    def is_cell_visible(
        self,
        row,
        col,
        player_row,
        player_col,
        visibility_radius,
    ):
        """
        Checks whether a cell is close enough to
        the player to be visible.

        Manhattan distance is used:
        vertical distance + horizontal distance.
        """

        row_distance = abs(
            row - player_row
        )

        col_distance = abs(
            col - player_col
        )

        total_distance = (
            row_distance + col_distance
        )

        return (
            total_distance
            <= visibility_radius
        )

    # =====================================================
    # DRAWING
    # =====================================================

    def draw(
        self,
        surface,
        player_row,
        player_col,
        visibility_radius,
    ):
        """
        Draws visible walls, paths and visited cells.
        """

        for row in range(self.rows):
            for col in range(self.cols):

                cell_rect = self.get_cell_rect(
                    row,
                    col,
                )

                visible = self.is_cell_visible(
                    row,
                    col,
                    player_row,
                    player_col,
                    visibility_radius,
                )

                visited = self.was_visited(
                    row,
                    col,
                )

                if visible:
                    self.draw_visible_cell(
                        surface,
                        row,
                        col,
                        cell_rect,
                    )

                elif visited:
                    self.draw_visited_cell(
                        surface,
                        cell_rect,
                    )

                else:
                    pygame.draw.rect(
                        surface,
                        HIDDEN_COLOR,
                        cell_rect,
                    )

    def draw_visible_cell(
        self,
        surface,
        row,
        col,
        cell_rect,
    ):
        """
        Draws a visible wall or visible path.
        """

        if self.is_wall(row, col):
            pygame.draw.rect(
                surface,
                WALL_COLOR,
                cell_rect,
            )

            pygame.draw.line(
                surface,
                WALL_EDGE,
                cell_rect.topleft,
                cell_rect.topright,
                width=1,
            )

            pygame.draw.line(
                surface,
                WALL_EDGE,
                cell_rect.topleft,
                cell_rect.bottomleft,
                width=1,
            )

        else:
            pygame.draw.rect(
                surface,
                PATH_COLOR,
                cell_rect,
            )

            pygame.draw.rect(
                surface,
                PATH_EDGE,
                cell_rect,
                width=1,
            )

    def draw_visited_cell(
        self,
        surface,
        cell_rect,
    ):
        """
        Draws a faint cell where the player has walked.
        """

        pygame.draw.rect(
            surface,
            VISITED_COLOR,
            cell_rect,
        )

        pygame.draw.rect(
            surface,
            PATH_EDGE,
            cell_rect,
            width=1,
        )