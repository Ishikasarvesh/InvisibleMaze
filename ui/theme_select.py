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


class WorldSelectScreen:
    """
    Renders a modern AAA carousel for World Selection with preview artwork,
    completion statistics, star counts, difficulty indicators, reflection graphics,
    and glowing focus animations.
    """

    def __init__(self, fonts, save_data):
        self.fonts = fonts
        self.save_data = save_data
        self.current_index = 0
        self.world_keys = ["1", "2", "3", "4", "5", "6"]
        self.animation_time = 0.0

        # Focus index based on unlocked progress
        self.recalculate_unlocked_index()

    def recalculate_unlocked_index(self):
        highest_unlocked = 0
        unlocked = self.save_data.get("unlocked_levels", ["1-1"])
        for idx, w in enumerate(self.world_keys):
            if f"{w}-1" in unlocked:
                highest_unlocked = idx
        self.current_index = highest_unlocked

    def update(self, delta_time):
        self.animation_time += delta_time

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.current_index = (self.current_index - 1) % len(self.world_keys)
                return ("change_theme", self.get_selected_world().theme_name)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.current_index = (self.current_index + 1) % len(self.world_keys)
                return ("change_theme", self.get_selected_world().theme_name)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                w_id = self.world_keys[self.current_index]
                if self.is_world_unlocked(w_id):
                    return ("select_world", w_id)
            elif event.key == pygame.K_ESCAPE:
                return ("back", None)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                cx = SCREEN_WIDTH // 2
                cy = SCREEN_HEIGHT // 2 + 10
                card_w, card_h = 260, 360
                gap = 280

                center_rect = pygame.Rect(cx - card_w // 2, cy - card_h // 2, card_w, card_h)
                left_rect = pygame.Rect(cx - gap - card_w // 2 + 20, cy - card_h // 2 + 30, card_w - 40, card_h - 60)
                right_rect = pygame.Rect(cx + gap - card_w // 2 + 20, cy - card_h // 2 + 30, card_w - 40, card_h - 60)

                back_rect = pygame.Rect(40, 40, 110, 42)
                if back_rect.collidepoint(mouse_pos):
                    return ("back", None)

                if center_rect.collidepoint(mouse_pos):
                    w_id = self.world_keys[self.current_index]
                    if self.is_world_unlocked(w_id):
                        return ("select_world", w_id)
                elif left_rect.collidepoint(mouse_pos):
                    self.current_index = (self.current_index - 1) % len(self.world_keys)
                    return ("change_theme", self.get_selected_world().theme_name)
                elif right_rect.collidepoint(mouse_pos):
                    self.current_index = (self.current_index + 1) % len(self.world_keys)
                    return ("change_theme", self.get_selected_world().theme_name)

        return None

    def get_selected_world(self):
        w_id = self.world_keys[self.current_index]
        return LevelManager.get_world(w_id)

    def is_world_unlocked(self, world_id):
        first_level = f"{world_id}-1"
        return first_level in self.save_data.get("unlocked_levels", ["1-1"])

    def get_world_stats(self, world_id):
        unlocked = self.save_data.get("unlocked_levels", ["1-1"])
        stars_dict = self.save_data.get("stars_earned", {})

        world_levels = [f"{world_id}-{i}" for i in range(1, 6)]
        unlocked_count = sum(1 for lvl in world_levels if lvl in unlocked)
        completion_pct = int((unlocked_count / 5.0) * 100)
        total_stars = sum(stars_dict.get(lvl, 0) for lvl in world_levels)

        return completion_pct, total_stars

    def draw(self, surface):
        surface.fill(BACKGROUND)

        # Header Title
        title_surf = self.fonts["heading"].render("SELECT WORLD", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 55))
        surface.blit(title_surf, title_rect)

        sub_surf = self.fonts["tiny"].render("Choose a Realm to Explore", True, TEXT_SECONDARY)
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 85)))

        # Back Button
        back_rect = pygame.Rect(40, 40, 110, 42)
        pygame.draw.rect(surface, PANEL, back_rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER, back_rect, width=2, border_radius=10)
        back_text = self.fonts["body"].render("< Back", True, WHITE)
        surface.blit(back_text, back_text.get_rect(center=back_rect.center))

        # Carousel parameters
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2 + 15
        card_w, card_h = 260, 360
        gap = 280

        indices_to_draw = [
            ((self.current_index - 1) % len(self.world_keys), cx - gap, False),
            ((self.current_index + 1) % len(self.world_keys), cx + gap, False),
            (self.current_index, cx, True),
        ]

        for idx, x_pos, is_center in indices_to_draw:
            w_id = self.world_keys[idx]
            world = LevelManager.get_world(w_id)
            unlocked = self.is_world_unlocked(w_id)
            completion_pct, total_stars = self.get_world_stats(w_id)

            w, h = (card_w, card_h) if is_center else (card_w - 40, card_h - 60)
            rect = pygame.Rect(x_pos - w // 2, cy - h // 2, w, h)

            # Pulsing aura glow for center card
            if is_center:
                pulse_val = (math.sin(self.animation_time * 5.0) + 1.0) / 2.0
                glow_rect = rect.inflate(int(14 + pulse_val * 8), int(14 + pulse_val * 8))
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 215, 0, 45), glow_surf.get_rect(), border_radius=18)
                surface.blit(glow_surf, glow_rect.topleft)

            # Card Background
            bg_color = (25, 30, 42) if is_center else PANEL
            pygame.draw.rect(surface, bg_color, rect, border_radius=16)

            border_color = YELLOW if is_center else (PANEL_BORDER if unlocked else (50, 50, 60))
            pygame.draw.rect(surface, border_color, rect, width=3 if is_center else 2, border_radius=16)

            # Artwork Preview Box
            preview_h = h // 2 - 10
            preview_rect = pygame.Rect(rect.left + 14, rect.top + 14, w - 28, preview_h)

            if unlocked:
                self.draw_preview_graphics(surface, preview_rect, world.theme_name)
            else:
                pygame.draw.rect(surface, (20, 20, 28), preview_rect, border_radius=10)
                lock_text = self.fonts["subheading"].render("LOCKED", True, RED)
                surface.blit(lock_text, lock_text.get_rect(center=preview_rect.center))

            # World Title Header
            name_color = WHITE if unlocked else TEXT_MUTED
            title_font = self.fonts["subheading"] if is_center else self.fonts["body"]
            world_name_surf = title_font.render(world.name, True, name_color)
            surface.blit(world_name_surf, world_name_surf.get_rect(center=(rect.centerx, rect.top + preview_h + 30)))

            # World Details: Completion & Stars
            if unlocked:
                stats_text = f"Progress: {completion_pct}%  ·  ★ {total_stars}/15"
                stats_surf = self.fonts["tiny"].render(stats_text, True, YELLOW if is_center else TEXT_SECONDARY)
                surface.blit(stats_surf, stats_surf.get_rect(center=(rect.centerx, rect.top + preview_h + 58)))

                diff_text = f"Difficulty: {'★' * int(w_id)}"
                diff_surf = self.fonts["tiny"].render(diff_text, True, BLUE if is_center else TEXT_MUTED)
                surface.blit(diff_surf, diff_surf.get_rect(center=(rect.centerx, rect.top + preview_h + 80)))
            else:
                req_text = f"Requires World {int(w_id) - 1}"
                req_surf = self.fonts["tiny"].render(req_text, True, TEXT_MUTED)
                surface.blit(req_surf, req_surf.get_rect(center=(rect.centerx, rect.top + preview_h + 65)))

            # Ground Reflection effect for center card
            if is_center:
                refl_h = 24
                refl_rect = pygame.Rect(rect.left, rect.bottom + 8, rect.width, refl_h)
                refl_surf = pygame.Surface(refl_rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(refl_surf, (0, 0, 0, 80), refl_surf.get_rect())
                surface.blit(refl_surf, refl_rect.topleft)

        # Bottom Hint Bar
        hint_text = "Use [A/D] or Left/Right Arrow Keys to Navigate Carousel  ·  Press ENTER to Select World"
        hint_surf = self.fonts["tiny"].render(hint_text, True, TEXT_MUTED)
        surface.blit(hint_surf, hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35)))

    def draw_preview_graphics(self, surface, rect, theme_name):
        pygame.draw.rect(surface, (15, 18, 25), rect, border_radius=10)

        # Render theme specific artwork patterns inside card
        if theme_name == "Ninja World":
            pygame.draw.rect(surface, (35, 20, 30), rect, border_radius=10)
            pygame.draw.circle(surface, (245, 82, 95, 120), rect.center, min(rect.width, rect.height) // 3)
            pygame.draw.line(surface, (255, 255, 255), (rect.left + 10, rect.bottom - 10), (rect.right - 10, rect.top + 10), width=2)
        elif theme_name == "Spring World":
            pygame.draw.rect(surface, (18, 40, 26), rect, border_radius=10)
            pygame.draw.circle(surface, (255, 182, 193), (rect.centerx - 15, rect.centery - 10), 14)
            pygame.draw.circle(surface, (69, 230, 154), (rect.centerx + 15, rect.centery + 10), 18)
        elif theme_name == "Frozen World":
            pygame.draw.rect(surface, (15, 30, 48), rect, border_radius=10)
            pygame.draw.polygon(surface, (140, 210, 255), [(rect.centerx, rect.top + 10), (rect.right - 15, rect.bottom - 15), (rect.left + 15, rect.bottom - 15)])
        elif theme_name == "Haunted World":
            pygame.draw.rect(surface, (25, 18, 35), rect, border_radius=10)
            pygame.draw.ellipse(surface, (160, 120, 210), (rect.centerx - 20, rect.centery - 20, 40, 40))
        elif theme_name == "Cyber World":
            pygame.draw.rect(surface, (10, 15, 30), rect, border_radius=10)
            for i in range(4):
                pygame.draw.line(surface, (0, 245, 255), (rect.left + 10 + i * 20, rect.top + 10), (rect.left + 10 + i * 20, rect.bottom - 10), width=1)
        elif theme_name == "Desert Temple World":
            pygame.draw.rect(surface, (45, 32, 18), rect, border_radius=10)
            pygame.draw.polygon(surface, (255, 210, 100), [(rect.centerx, rect.top + 15), (rect.right - 20, rect.bottom - 10), (rect.left + 20, rect.bottom - 10)])
