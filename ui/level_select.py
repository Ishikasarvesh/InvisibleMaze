import pygame
import math
from game.levels import LevelManager
from game.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    YELLOW,
    BLUE,
    RED,
    GREEN,
    PANEL,
    PANEL_BORDER,
    TEXT_MUTED,
    TEXT_SECONDARY,
    BACKGROUND,
)


class LevelSelectScreen:
    """
    Renders an interactive World Map layout with connected level nodes (1 -> 2 -> 3 -> 4 -> Boss),
    star badges, boss icons, personal best scores, and glowing node selection paths.
    """

    def __init__(self, fonts, save_data, world_id):
        self.fonts = fonts
        self.save_data = save_data
        self.world_id = str(world_id)
        self.selected_index = 0
        self.animation_time = 0.0

        # Fetch configurations
        self.world = LevelManager.get_world(self.world_id)
        self.levels = self.world.levels

        # Focus index on the latest unlocked level in this world
        self.recalculate_unlocked_index()

    def recalculate_unlocked_index(self):
        highest_unlocked = 0
        unlocked = self.save_data.get("unlocked_levels", ["1-1"])
        for idx, lvl in enumerate(self.levels):
            if lvl.level_id in unlocked:
                highest_unlocked = idx
        self.selected_index = highest_unlocked

    def update(self, delta_time):
        self.animation_time += delta_time

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.levels)
                return None
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.levels)
                return None
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                lvl = self.levels[self.selected_index]
                if lvl.level_id in self.save_data.get("unlocked_levels", ["1-1"]):
                    return ("start_level", lvl.level_id)
            elif event.key == pygame.K_ESCAPE:
                return ("back_to_worlds", None)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                back_rect = pygame.Rect(40, 40, 110, 42)
                if back_rect.collidepoint(mouse_pos):
                    return ("back_to_worlds", None)

                nodes_positions = self.get_nodes_positions()
                for idx, pos in enumerate(nodes_positions):
                    node_rect = pygame.Rect(pos[0] - 40, pos[1] - 40, 80, 80)
                    if node_rect.collidepoint(mouse_pos):
                        lvl = self.levels[idx]
                        if lvl.level_id in self.save_data.get("unlocked_levels", ["1-1"]):
                            if self.selected_index == idx:
                                return ("start_level", lvl.level_id)
                            else:
                                self.selected_index = idx
                        return None

        return None

    def get_nodes_positions(self):
        """
        Returns curved organic horizontal coordinates for connected world map nodes.
        """
        positions = []
        start_x = 180
        end_x = SCREEN_WIDTH - 180
        spacing = (end_x - start_x) // 4
        y_pos = SCREEN_HEIGHT // 2 - 10

        for i in range(5):
            y_offset = int(math.sin(i * 1.4) * 50)
            positions.append((start_x + i * spacing, y_pos + y_offset))
        return positions

    def draw(self, surface):
        surface.fill(BACKGROUND)

        # Header Title
        world_title = f"WORLD {self.world_id}: {self.world.name.upper()}"
        title_surf = self.fonts["heading"].render(world_title, True, WHITE)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 55)))

        sub_surf = self.fonts["tiny"].render("Select a Stage Node to Enter the Maze", True, TEXT_SECONDARY)
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 85)))

        # Back Button
        back_rect = pygame.Rect(40, 40, 110, 42)
        pygame.draw.rect(surface, PANEL, back_rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER, back_rect, width=2, border_radius=10)
        back_text = self.fonts["body"].render("< Back", True, WHITE)
        surface.blit(back_text, back_text.get_rect(center=back_rect.center))

        positions = self.get_nodes_positions()
        unlocked_set = self.save_data.get("unlocked_levels", ["1-1"])

        # 1. Draw paths connecting nodes
        for i in range(len(positions) - 1):
            start = positions[i]
            end = positions[i + 1]
            next_lvl = self.levels[i + 1]
            unlocked = next_lvl.level_id in unlocked_set

            line_color = BLUE if unlocked else (45, 45, 55)
            pygame.draw.line(surface, line_color, start, end, width=6)

            if unlocked:
                # Add glowing pulse along active path
                pulse_pos_t = (math.sin(self.animation_time * 3.0 + i) + 1.0) / 2.0
                px = int(start[0] + (end[0] - start[0]) * pulse_pos_t)
                py = int(start[1] + (end[1] - start[1]) * pulse_pos_t)
                pygame.draw.circle(surface, (120, 200, 255), (px, py), 4)

        # 2. Draw nodes
        for idx, pos in enumerate(positions):
            lvl = self.levels[idx]
            unlocked = lvl.level_id in unlocked_set
            is_selected = (idx == self.selected_index)

            node_r = 34
            node_color = (25, 30, 42) if unlocked else PANEL
            border_color = (55, 55, 65)

            if unlocked:
                border_color = BLUE
                if lvl.is_boss_level:
                    border_color = RED

            if is_selected:
                pulse_val = (math.sin(self.animation_time * 7.0) + 1.0) / 2.0
                glow_r = int(node_r + 8 + pulse_val * 6)
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 215, 0, 50), (glow_r, glow_r), glow_r)
                surface.blit(glow_surf, (pos[0] - glow_r, pos[1] - glow_r))
                border_color = YELLOW

            pygame.draw.circle(surface, node_color, pos, node_r)
            pygame.draw.circle(surface, border_color, pos, node_r, width=4 if is_selected else 2)

            # Node label/icon
            if unlocked:
                node_text = "BOSS" if lvl.is_boss_level else str(idx + 1)
                text_color = RED if (lvl.is_boss_level and not is_selected) else (YELLOW if is_selected else WHITE)
                node_text_surf = self.fonts["subheading"].render(node_text, True, text_color)
                surface.blit(node_text_surf, node_text_surf.get_rect(center=pos))
            else:
                # Lock Symbol
                pygame.draw.rect(surface, (70, 70, 80), (pos[0] - 7, pos[1] - 2, 14, 12), border_radius=2)
                pygame.draw.circle(surface, (70, 70, 80), (pos[0], pos[1] - 2), 6, width=2)

            # Star Badges above Node
            if unlocked:
                stars = self.save_data.get("stars_earned", {}).get(lvl.level_id, 0)
                stars_y = pos[1] - 46
                for s_i in range(3):
                    star_x = pos[0] + (s_i - 1) * 16
                    color = YELLOW if s_i < stars else (70, 70, 80)
                    star_surf = self.fonts["tiny"].render("★", True, color)
                    surface.blit(star_surf, star_surf.get_rect(center=(star_x, stars_y)))

        # 3. Display Detailed Level Info Panel at Bottom for Focused Node
        selected_lvl = self.levels[self.selected_index]
        card_y = SCREEN_HEIGHT - 135
        card_w, card_h = 420, 95
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, card_y, card_w, card_h)

        pygame.draw.rect(surface, PANEL, card_rect, border_radius=14)
        pygame.draw.rect(surface, PANEL_BORDER, card_rect, width=2, border_radius=14)

        # Name
        lvl_unlocked = selected_lvl.level_id in unlocked_set
        title_color = WHITE if lvl_unlocked else RED
        name_surf = self.fonts["body"].render(f"Stage {selected_lvl.level_number}: {selected_lvl.display_name}", True, title_color)
        surface.blit(name_surf, (card_rect.left + 18, card_rect.top + 12))

        # Target Specs
        specs_text = f"Time Target: {selected_lvl.time_target}s  ·  Move Limit: {selected_lvl.move_target} moves"
        specs_surf = self.fonts["tiny"].render(specs_text, True, TEXT_SECONDARY)
        surface.blit(specs_surf, (card_rect.left + 18, card_rect.top + 38))

        # Personal Best
        hi_score = self.save_data.get("highest_score", {}).get(selected_lvl.level_id, 0)
        score_surf = self.fonts["tiny"].render(f"Personal Best: {hi_score} pts", True, BLUE)
        surface.blit(score_surf, (card_rect.left + 18, card_rect.top + 60))

        # Start prompt button
        if lvl_unlocked:
            prompt_text = "Press ENTER to Play!"
            prompt_surf = self.fonts["tiny"].render(prompt_text, True, YELLOW)
            surface.blit(prompt_surf, prompt_surf.get_rect(right=card_rect.right - 18, centery=card_rect.centery))
        else:
            prompt_text = "STAGE LOCKED"
            prompt_surf = self.fonts["tiny"].render(prompt_text, True, RED)
            surface.blit(prompt_surf, prompt_surf.get_rect(right=card_rect.right - 18, centery=card_rect.centery))

        # Navigation hint
        nav_hint = "Use [A/D] or Arrow Keys to Select Node  ·  Press ENTER to Launch Level"
        nav_surf = self.fonts["tiny"].render(nav_hint, True, TEXT_MUTED)
        surface.blit(nav_surf, nav_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 22)))
