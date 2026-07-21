import pygame

from game.animations import AnimatedValue, pulse
from game.settings import (
    BLUE,
    ORANGE,
    PANEL,
    PANEL_BORDER,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_MUTED,
    TEXT_SECONDARY,
    WHITE,
    YELLOW,
)
from ui.button import AnimatedButton


class PauseScreen:
    """
    Displays a pause overlay above the current game screen.

    Available actions:
    - Continue the game
    - Restart the current level
    - Return to the main menu
    """

    def __init__(self, fonts):
        self.fonts = fonts

        self.animation_time = 0

        # Controls the dark overlay opacity.
        self.overlay_alpha = AnimatedValue(0)

        # Controls the panel entrance animation.
        self.panel_progress = AnimatedValue(0)

        # Controls the title animation.
        self.title_progress = AnimatedValue(0)

        panel_width = 470
        panel_height = 500

        self.panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - panel_width // 2,
            SCREEN_HEIGHT // 2 - panel_height // 2,
            panel_width,
            panel_height,
        )

        button_width = 300
        button_height = 46
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        start_y = self.panel_rect.y + 190
        gap = 58

        self.continue_button = AnimatedButton(
            button_x,
            start_y,
            button_width,
            button_height,
            "Resume",
            self.fonts["body"],
            subtitle="",
        )

        self.restart_button = AnimatedButton(
            button_x,
            start_y + gap,
            button_width,
            button_height,
            "Restart Level",
            self.fonts["body"],
            subtitle="",
        )

        self.world_map_button = AnimatedButton(
            button_x,
            start_y + gap * 2,
            button_width,
            button_height,
            "World Map",
            self.fonts["body"],
            subtitle="",
        )

        self.settings_button = AnimatedButton(
            button_x,
            start_y + gap * 3,
            button_width,
            button_height,
            "Settings",
            self.fonts["body"],
            subtitle="",
        )

        self.menu_button = AnimatedButton(
            button_x,
            start_y + gap * 4,
            button_width,
            button_height,
            "Main Menu",
            self.fonts["body"],
            subtitle="",
        )

        self.buttons = [
            self.continue_button,
            self.restart_button,
            self.world_map_button,
            self.settings_button,
            self.menu_button,
        ]

        self.open()

    # =====================================================
    # OPEN PAUSE SCREEN
    # =====================================================

    def open(self):
        """
        Starts panel transitions.
        """
        self.animation_time = 0
        self.overlay_alpha.snap(0)
        self.overlay_alpha.set_target(185)

        self.panel_progress.snap(0)
        self.panel_progress.set_target(1)

        self.title_progress.snap(0)
        self.title_progress.set_target(1)

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, delta_time):
        """
        Updates animation elements.
        """
        self.animation_time += delta_time

        self.panel_progress.update(
            delta_time,
            speed=7,
        )

        self.overlay_alpha.update(
            delta_time,
            speed=6,
        )

        self.title_progress.update(
            delta_time,
            speed=6,
        )

        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(
                delta_time,
                mouse_position,
            )

    # =====================================================
    # EVENT HANDLING
    # =====================================================

    def handle_event(self, event):
        """
        Handles mouse and keyboard input.
        """
        if self.continue_button.handle_event(event):
            return "continue"

        if self.restart_button.handle_event(event):
            return "restart"

        if self.world_map_button.handle_event(event):
            return "world_map"

        if self.settings_button.handle_event(event):
            return "settings"

        if self.menu_button.handle_event(event):
            return "menu"

        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_p,
                pygame.K_ESCAPE,
            ):
                return "continue"

            if event.key == pygame.K_r:
                return "restart"

            if event.key == pygame.K_w:
                return "world_map"

            if event.key == pygame.K_s:
                return "settings"

            if event.key == pygame.K_m:
                return "menu"

        return None

    # =====================================================
    # OVERLAY
    # =====================================================

    def draw_overlay(self, surface):
        """
        Draws a transparent black layer above the game.
        """

        overlay = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (
                5,
                8,
                16,
                int(self.overlay_alpha.value),
            )
        )

        surface.blit(
            overlay,
            (0, 0),
        )

    # =====================================================
    # PANEL
    # =====================================================

    def get_animated_panel_rect(self):
        """
        Returns a panel rectangle with an entrance animation.
        """

        progress = max(
            0,
            min(
                1,
                self.panel_progress.value,
            ),
        )

        animated_width = max(
            1,
            int(
                self.panel_rect.width
                * (
                    0.85
                    + progress * 0.15
                )
            ),
        )

        animated_height = max(
            1,
            int(
                self.panel_rect.height
                * (
                    0.85
                    + progress * 0.15
                )
            ),
        )

        animated_rect = pygame.Rect(
            0,
            0,
            animated_width,
            animated_height,
        )

        animated_rect.center = (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )

        return animated_rect

    def draw_panel(self, surface):
        """
        Draws the central pause panel.
        """

        animated_rect = self.get_animated_panel_rect()

        shadow_rect = animated_rect.copy()
        shadow_rect.y += 10

        shadow_surface = pygame.Surface(
            (
                shadow_rect.width,
                shadow_rect.height,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.rect(
            shadow_surface,
            (
                0,
                0,
                0,
                110,
            ),
            shadow_surface.get_rect(),
            border_radius=28,
        )

        surface.blit(
            shadow_surface,
            shadow_rect,
        )

        panel_surface = pygame.Surface(
            (
                animated_rect.width,
                animated_rect.height,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.rect(
            panel_surface,
            (
                PANEL[0],
                PANEL[1],
                PANEL[2],
                245,
            ),
            panel_surface.get_rect(),
            border_radius=28,
        )

        pygame.draw.rect(
            panel_surface,
            PANEL_BORDER,
            panel_surface.get_rect(),
            width=2,
            border_radius=28,
        )

        surface.blit(
            panel_surface,
            animated_rect,
        )

    # =====================================================
    # DECORATION
    # =====================================================

    def draw_pause_icon(self, surface):
        """
        Draws an animated pause symbol.
        """

        icon_center_x = SCREEN_WIDTH // 2
        icon_center_y = self.panel_rect.y + 84

        icon_scale = pulse(
            self.animation_time,
            speed=2.5,
            minimum=0.94,
            maximum=1.06,
        )

        circle_radius = int(
            38 * icon_scale
        )

        glow_surface = pygame.Surface(
            (
                circle_radius * 4,
                circle_radius * 4,
            ),
            pygame.SRCALPHA,
        )

        glow_center = (
            glow_surface.get_width() // 2,
            glow_surface.get_height() // 2,
        )

        pygame.draw.circle(
            glow_surface,
            (
                BLUE[0],
                BLUE[1],
                BLUE[2],
                35,
            ),
            glow_center,
            circle_radius + 18,
        )

        pygame.draw.circle(
            glow_surface,
            (
                BLUE[0],
                BLUE[1],
                BLUE[2],
                75,
            ),
            glow_center,
            circle_radius,
        )

        surface.blit(
            glow_surface,
            (
                icon_center_x
                - glow_surface.get_width() // 2,
                icon_center_y
                - glow_surface.get_height() // 2,
            ),
        )

        bar_width = 8
        bar_height = 30
        bar_gap = 10

        left_bar = pygame.Rect(
            icon_center_x
            - bar_gap
            - bar_width,
            icon_center_y
            - bar_height // 2,
            bar_width,
            bar_height,
        )

        right_bar = pygame.Rect(
            icon_center_x
            + bar_gap,
            icon_center_y
            - bar_height // 2,
            bar_width,
            bar_height,
        )

        pygame.draw.rect(
            surface,
            WHITE,
            left_bar,
            border_radius=4,
        )

        pygame.draw.rect(
            surface,
            WHITE,
            right_bar,
            border_radius=4,
        )

    # =====================================================
    # TEXT
    # =====================================================

    def draw_text(self, surface):
        """
        Draws the pause title and instructions.
        """

        alpha = int(
            255
            * max(
                0,
                min(
                    1,
                    self.title_progress.value,
                ),
            )
        )

        title_surface = self.fonts[
            "heading"
        ].render(
            "GAME PAUSED",
            True,
            WHITE,
        )

        title_surface.set_alpha(alpha)

        title_rect = title_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                self.panel_rect.y + 150,
            )
        )

        surface.blit(
            title_surface,
            title_rect,
        )

        subtitle_surface = self.fonts[
            "small"
        ].render(
            "Your torch has stopped draining.",
            True,
            TEXT_SECONDARY,
        )

        subtitle_surface.set_alpha(alpha)

        subtitle_rect = subtitle_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                self.panel_rect.y + 190,
            )
        )

        surface.blit(
            subtitle_surface,
            subtitle_rect,
        )

    def draw_keyboard_hint(self, surface):
        """
        Draws the keyboard shortcut hint.
        """

        hint_text = (
            "P / Esc: Continue   "
            "R: Restart   "
            "M: Menu"
        )

        hint_surface = self.fonts[
            "tiny"
        ].render(
            hint_text,
            True,
            TEXT_MUTED,
        )

        hint_rect = hint_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                self.panel_rect.bottom - 20,
            )
        )

        surface.blit(
            hint_surface,
            hint_rect,
        )

    # =====================================================
    # DRAW
    # =====================================================

    def draw(self, surface):
        """
        Draws the full pause screen.
        """

        self.draw_overlay(surface)
        self.draw_panel(surface)
        self.draw_pause_icon(surface)
        self.draw_text(surface)

        for button in self.buttons:
            button.draw(surface)

        self.draw_keyboard_hint(surface)