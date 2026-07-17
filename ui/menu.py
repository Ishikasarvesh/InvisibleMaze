import math

import pygame

from game.animations import AnimatedValue, floating_offset, pulse
from game.settings import (
    BACKGROUND,
    BACKGROUND_SECONDARY,
    BLUE,
    GREEN,
    ORANGE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_MUTED,
    TEXT_SECONDARY,
    WHITE,
    YELLOW,
)
from ui.button import AnimatedButton


class MainMenu:
    """
    Draws and controls the animated main menu.
    """

    def __init__(
        self,
        fonts,
        particle_manager,
    ):
        self.fonts = fonts
        self.particle_manager = particle_manager

        self.animation_time = 0

        self.title_offset = AnimatedValue(-40)
        self.title_alpha = AnimatedValue(0)

        self.subtitle_offset = AnimatedValue(25)
        self.subtitle_alpha = AnimatedValue(0)

        self.card_progress = [
            AnimatedValue(0),
            AnimatedValue(0),
            AnimatedValue(0),
        ]

        card_width = 260
        card_height = 165
        gap = 25

        total_width = (
            card_width * 3
            + gap * 2
        )

        start_x = (
            SCREEN_WIDTH - total_width
        ) // 2

        card_y = 350

        self.easy_button = AnimatedButton(
            start_x,
            card_y,
            card_width,
            card_height,
            "Easy",
            self.fonts["subheading"],
            subtitle="Large torch · More batteries",
        )

        self.medium_button = AnimatedButton(
            start_x + card_width + gap,
            card_y,
            card_width,
            card_height,
            "Medium",
            self.fonts["subheading"],
            subtitle="Balanced maze challenge",
        )

        self.hard_button = AnimatedButton(
            start_x + (card_width + gap) * 2,
            card_y,
            card_width,
            card_height,
            "Hard",
            self.fonts["subheading"],
            subtitle="Low light · Fewer batteries",
        )

        self.buttons = [
            self.easy_button,
            self.medium_button,
            self.hard_button,
        ]

        self.settings_button = AnimatedButton(
            SCREEN_WIDTH // 2 - 100,
            560,
            200,
            56,
            "Settings",
            self.fonts["body"],
        )

        self.title_offset.set_target(0)
        self.title_alpha.set_target(1)

        self.subtitle_offset.set_target(0)
        self.subtitle_alpha.set_target(1)

        for index, progress in enumerate(
            self.card_progress
        ):
            progress.set_target(1)

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, delta_time):
        self.animation_time += delta_time

        mouse_position = pygame.mouse.get_pos()

        self.title_offset.update(
            delta_time,
            speed=5,
        )

        self.title_alpha.update(
            delta_time,
            speed=4,
        )

        self.subtitle_offset.update(
            delta_time,
            speed=5,
        )

        self.subtitle_alpha.update(
            delta_time,
            speed=4,
        )

        for progress in self.card_progress:
            progress.update(
                delta_time,
                speed=5,
            )

        for button in self.buttons:
            button.update(
                delta_time,
                mouse_position,
            )

        self.settings_button.update(
            delta_time,
            mouse_position,
        )

    # =====================================================
    # EVENTS
    # =====================================================

    def handle_event(self, event):
        if self.easy_button.handle_event(event):
            return ("start", "Easy")

        if self.medium_button.handle_event(event):
            return ("start", "Medium")

        if self.hard_button.handle_event(event):
            return ("start", "Hard")

        if self.settings_button.handle_event(event):
            return ("settings", None)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return ("start", "Easy")

            if event.key == pygame.K_2:
                return ("start", "Medium")

            if event.key == pygame.K_3:
                return ("start", "Hard")

            if event.key == pygame.K_s:
                return ("settings", None)

        return None

    # =====================================================
    # BACKGROUND
    # =====================================================

    def draw_background(self, surface):
        surface.fill(BACKGROUND)

        overlay = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        center_x = SCREEN_WIDTH // 2
        center_y = 180

        pulse_radius = int(
            pulse(
                self.animation_time,
                speed=1.8,
                minimum=180,
                maximum=230,
            )
        )

        pygame.draw.circle(
            overlay,
            (
                255,
                210,
                90,
                18,
            ),
            (
                center_x,
                center_y,
            ),
            pulse_radius,
        )

        pygame.draw.circle(
            overlay,
            (
                85,
                135,
                255,
                12,
            ),
            (
                center_x - 230,
                center_y + 160,
            ),
            210,
        )

        pygame.draw.circle(
            overlay,
            (
                60,
                230,
                165,
                10,
            ),
            (
                center_x + 270,
                center_y + 190,
            ),
            190,
        )

        surface.blit(
            overlay,
            (0, 0),
        )

        self.draw_grid_pattern(surface)

    def draw_grid_pattern(self, surface):
        grid_surface = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        spacing = 42

        for x in range(
            0,
            SCREEN_WIDTH,
            spacing,
        ):
            pygame.draw.line(
                grid_surface,
                (
                    100,
                    120,
                    170,
                    9,
                ),
                (
                    x,
                    0,
                ),
                (
                    x,
                    SCREEN_HEIGHT,
                ),
            )

        for y in range(
            0,
            SCREEN_HEIGHT,
            spacing,
        ):
            pygame.draw.line(
                grid_surface,
                (
                    100,
                    120,
                    170,
                    9,
                ),
                (
                    0,
                    y,
                ),
                (
                    SCREEN_WIDTH,
                    y,
                ),
            )

        surface.blit(
            grid_surface,
            (0, 0),
        )

    # =====================================================
    # TITLE
    # =====================================================

    def draw_title(self, surface):
        floating = floating_offset(
            self.animation_time,
            speed=1.7,
            distance=6,
        )

        title_surface = self.fonts["title"].render(
            "INVISIBLE MAZE",
            True,
            WHITE,
        )

        title_surface.set_alpha(
            int(
                255
                * self.title_alpha.value
            )
        )

        title_rect = title_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                int(
                    145
                    + self.title_offset.value
                    + floating
                ),
            )
        )

        glow_surface = pygame.Surface(
            (
                title_rect.width + 70,
                title_rect.height + 50,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.ellipse(
            glow_surface,
            (
                255,
                216,
                110,
                28,
            ),
            glow_surface.get_rect(),
        )

        surface.blit(
            glow_surface,
            (
                title_rect.x - 35,
                title_rect.y - 25,
            ),
        )

        surface.blit(
            title_surface,
            title_rect,
        )

        subtitle = (
            "Find the exit before your torch fades."
        )

        subtitle_surface = self.fonts[
            "body"
        ].render(
            subtitle,
            True,
            TEXT_SECONDARY,
        )

        subtitle_surface.set_alpha(
            int(
                255
                * self.subtitle_alpha.value
            )
        )

        subtitle_rect = (
            subtitle_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    int(
                        235
                        + self.subtitle_offset.value
                    ),
                )
            )
        )

        surface.blit(
            subtitle_surface,
            subtitle_rect,
        )

        hint_surface = self.fonts[
            "small"
        ].render(
            "Choose your difficulty",
            True,
            TEXT_MUTED,
        )

        surface.blit(
            hint_surface,
            hint_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    290,
                )
            ),
        )

    # =====================================================
    # DIFFICULTY CARDS
    # =====================================================

    def draw_difficulty_badges(
        self,
        surface,
    ):
        badge_data = [
            (
                self.easy_button.base_rect,
                GREEN,
                "17 × 17",
            ),
            (
                self.medium_button.base_rect,
                YELLOW,
                "21 × 21",
            ),
            (
                self.hard_button.base_rect,
                ORANGE,
                "25 × 25",
            ),
        ]

        for index, (
            rect,
            color,
            text,
        ) in enumerate(badge_data):
            progress = self.card_progress[
                index
            ].value

            badge_width = 78
            badge_height = 28

            badge_rect = pygame.Rect(
                rect.right
                - badge_width
                - 14,
                rect.top + 14,
                badge_width,
                badge_height,
            )

            badge_surface = pygame.Surface(
                (
                    badge_width,
                    badge_height,
                ),
                pygame.SRCALPHA,
            )

            pygame.draw.rect(
                badge_surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    int(45 * progress),
                ),
                badge_surface.get_rect(),
                border_radius=14,
            )

            badge_text = self.fonts[
                "tiny"
            ].render(
                text,
                True,
                color,
            )

            badge_surface.blit(
                badge_text,
                badge_text.get_rect(
                    center=(
                        badge_width // 2,
                        badge_height // 2,
                    )
                ),
            )

            surface.blit(
                badge_surface,
                badge_rect,
            )

    # =====================================================
    # FOOTER
    # =====================================================

    def draw_footer(self, surface):
        control_text = (
            "Move with WASD or Arrow Keys  ·  "
            "Pause with P  ·  Restart with R"
        )

        control_surface = self.fonts[
            "small"
        ].render(
            control_text,
            True,
            TEXT_MUTED,
        )

        surface.blit(
            control_surface,
            control_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    SCREEN_HEIGHT - 46,
                )
            ),
        )

        version_surface = self.fonts[
            "tiny"
        ].render(
            "Version 3.0",
            True,
            TEXT_MUTED,
        )

        surface.blit(
            version_surface,
            (
                SCREEN_WIDTH
                - version_surface.get_width()
                - 22,
                SCREEN_HEIGHT
                - version_surface.get_height()
                - 18,
            ),
        )

    # =====================================================
    # DRAW
    # =====================================================

    def draw(self, surface):
        self.draw_background(surface)

        self.particle_manager.draw_fireflies(
            surface
        )

        self.draw_title(surface)

        for button in self.buttons:
            button.draw(surface)

        self.draw_difficulty_badges(surface)

        self.settings_button.draw(surface)

        self.draw_footer(surface)