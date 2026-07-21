import random
import pygame

import game.settings
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
    Generates and stores the maze grid layout.
    0 = Path
    1 = Wall
    """

    def __init__(
        self,
        rows=15,
        cols=15,
        cell_size=40,
        start_x=0,
        start_y=0,
        **kwargs,
    ):
        self.rows = self.ensure_odd(rows)
        self.cols = self.ensure_odd(cols)

        self.grid = []

        self.visited_cells = set()
        self.cell_size = cell_size
        self.start_x = start_x
        self.start_y = start_y

        self.generate()

    # =====================================================
    # GRID INITIALIZATION
    # =====================================================

    def ensure_odd(self, value):
        """
        Maze generation requires odd dimensions.
        """
        if value % 2 == 0:
            return value + 1
        return value

    def create_empty_grid(self):
        """
        Creates a grid filled with walls.
        """
        self.grid = [
            [1 for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

    # =====================================================
    # MAZE GENERATION
    # =====================================================

    def generate(self):
        """
        Generates a solvable maze using Depth-First Search.
        """
        self.create_empty_grid()
        self.visited_cells.clear()

        start_row, start_col = 1, 1
        self.grid[start_row][start_col] = 0

        stack = [(start_row, start_col)]

        while stack:
            current_row, current_col = stack[-1]

            neighbors = self.get_unvisited_neighbors(
                current_row,
                current_col,
            )

            if neighbors:
                next_row, next_col, wall_row, wall_col = random.choice(
                    neighbors
                )

                self.grid[wall_row][wall_col] = 0
                self.grid[next_row][next_col] = 0

                stack.append((next_row, next_col))
            else:
                stack.pop()

    def get_unvisited_neighbors(
        self,
        row,
        col,
    ):
        """
        Finds neighbor cells two steps away that are still walls.
        """
        neighbors = []

        directions = [
            (-2, 0),
            (2, 0),
            (0, -2),
            (0, 2),
        ]

        for row_change, col_change in directions:
            target_row = row + row_change
            target_col = col + col_change
            wall_row = row + row_change // 2
            wall_col = col + col_change // 2

            if self.is_valid_cell(
                target_row,
                target_col,
            ):
                if self.grid[target_row][target_col] == 1:
                    neighbors.append(
                        (
                            target_row,
                            target_col,
                            wall_row,
                            wall_col,
                        )
                    )

        return neighbors

    def is_valid_cell(
        self,
        row,
        col,
    ):
        """
        Checks if a cell is inside the inner maze grid.
        """
        return (
            0 < row < self.rows - 1
            and 0 < col < self.cols - 1
        )

    # =====================================================
    # CELL TYPES AND RECTS
    # =====================================================

    def is_wall(
        self,
        row,
        col,
    ):
        if not (
            0 <= row < self.rows
            and 0 <= col < self.cols
        ):
            return True

        return self.grid[row][col] == 1

    def is_path(
        self,
        row,
        col,
    ):
        return not self.is_wall(
            row,
            col,
        )

    def calculate_cell_size(
        self,
        available_width,
        available_height,
    ):
        """
        Calculates cell size to fit the window.
        """
        size_x = available_width // self.cols
        size_y = available_height // self.rows

        self.cell_size = max(
            12,
            min(size_x, size_y),
        )

        return self.cell_size

    def get_cell_rect(
        self,
        row,
        col,
    ):
        """
        Returns the pixel rectangle for a cell.
        """
        start_x = getattr(self, "start_x", 0)
        start_y = getattr(self, "start_y", 0)
        x = start_x + col * self.cell_size
        y = start_y + row * self.cell_size

        return pygame.Rect(
            x,
            y,
            self.cell_size,
            self.cell_size,
        )

    def get_cell_center(
        self,
        row,
        col,
    ):
        """
        Returns the center pixel position of a cell.
        """
        rect = self.get_cell_rect(
            row,
            col,
        )

        return (
            rect.centerx,
            rect.centery,
        )

    # =====================================================
    # VISIBILITY & VISITED
    # =====================================================

    def mark_visited(
        self,
        row,
        col,
    ):
        """
        Remembers cells the player has walked over.
        """
        self.visited_cells.add((row, col))

    def was_visited(
        self,
        row,
        col,
    ):
        return (row, col) in self.visited_cells

    def is_cell_visible(
        self,
        row,
        col,
        player_row,
        player_col,
        visibility_radius,
    ):
        """
        Checks if a cell is within visibility range.
        """
        row_distance = abs(row - player_row)
        col_distance = abs(col - player_col)

        distance = row_distance + col_distance

        return distance <= visibility_radius

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
        debug_grid = getattr(game.settings, "DEBUG_DRAW_GRID", False)

        for row in range(self.rows):
            for col in range(self.cols):
                cell_rect = self.get_cell_rect(row, col)
                visible = self.is_cell_visible(row, col, player_row, player_col, visibility_radius)
                visited = self.was_visited(row, col)

                if visible:
                    self.draw_visible_cell(surface, row, col, cell_rect, debug_grid)
                elif visited:
                    self.draw_visited_cell(surface, cell_rect, debug_grid)
                else:
                    pygame.draw.rect(surface, (0, 0, 0), cell_rect)

    def draw_visible_cell(
        self,
        surface,
        row,
        col,
        cell_rect,
        debug_grid=False,
    ):
        """
        Draws a visible wall or visible path without debug grid boxes.
        """
        if self.is_wall(row, col):
            pygame.draw.rect(
                surface,
                WALL_COLOR,
                cell_rect,
            )
        else:
            pygame.draw.rect(
                surface,
                PATH_COLOR,
                cell_rect,
            )

        if debug_grid:
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
        debug_grid=False,
    ):
        """
        Draws a faint cell where the player has walked without debug grid boxes.
        """
        pygame.draw.rect(
            surface,
            VISITED_COLOR,
            cell_rect,
        )

        if debug_grid:
            pygame.draw.rect(
                surface,
                PATH_EDGE,
                cell_rect,
                width=1,
            )