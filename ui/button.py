import pygame

from game.animations import AnimatedValue
from game.settings import (
    BLUE,
    BLUE_LIGHT,
    PANEL,
    PANEL_BORDER,
    PANEL_HOVER,
    TEXT_SECONDARY,
    WHITE,
)


class AnimatedButton:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        font,
        subtitle=None,
        icon=None,
    ):
        self.base_rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.text = text
        self.subtitle = subtitle
        self.icon = icon
        self.font = font

        self.hovered = False
        self.pressed = False
        self.enabled = True

        self.scale = AnimatedValue(1)
        self.border_progress = AnimatedValue(0)
        self.hover_progress = AnimatedValue(0)

    def update(self, delta_time, mouse_position):
        self.hovered = (
            self.enabled
            and self.base_rect.collidepoint(
                mouse_position
            )
        )

        if self.hovered:
            self.scale.set_target(1.035)
            self.border_progress.set_target(1)
            self.hover_progress.set_target(1)
        else:
            self.scale.set_target(1)
            self.border_progress.set_target(0)
            self.hover_progress.set_target(0)

        if self.pressed:
            self.scale.set_target(0.97)

        self.scale.update(delta_time, speed=10)
        self.border_progress.update(delta_time, speed=8)
        self.hover_progress.update(delta_time, speed=8)

    def get_animated_rect(self):
        width = int(
            self.base_rect.width
            * self.scale.value
        )

        height = int(
            self.base_rect.height
            * self.scale.value
        )

        animated_rect = pygame.Rect(
            0,
            0,
            width,
            height
        )

        animated_rect.center = self.base_rect.center

        return animated_rect

    def draw(self, surface):
        animated_rect = self.get_animated_rect()

        hover_value = self.hover_progress.value

        background_color = (
            int(
                PANEL[0]
                + (
                    PANEL_HOVER[0] - PANEL[0]
                ) * hover_value
            ),
            int(
                PANEL[1]
                + (
                    PANEL_HOVER[1] - PANEL[1]
                ) * hover_value
            ),
            int(
                PANEL[2]
                + (
                    PANEL_HOVER[2] - PANEL[2]
                ) * hover_value
            ),
        )

        shadow_rect = animated_rect.copy()
        shadow_rect.y += 7

        shadow_surface = pygame.Surface(
            (
                shadow_rect.width + 20,
                shadow_rect.height + 20
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            shadow_surface,
            (0, 0, 0, 90),
            pygame.Rect(
                10,
                10,
                shadow_rect.width,
                shadow_rect.height
            ),
            border_radius=16
        )

        surface.blit(
            shadow_surface,
            (
                shadow_rect.x - 10,
                shadow_rect.y - 10
            )
        )

        pygame.draw.rect(
            surface,
            background_color,
            animated_rect,
            border_radius=16
        )

        border_color = (
            int(
                PANEL_BORDER[0]
                + (
                    BLUE_LIGHT[0] - PANEL_BORDER[0]
                ) * self.border_progress.value
            ),
            int(
                PANEL_BORDER[1]
                + (
                    BLUE_LIGHT[1] - PANEL_BORDER[1]
                ) * self.border_progress.value
            ),
            int(
                PANEL_BORDER[2]
                + (
                    BLUE_LIGHT[2] - PANEL_BORDER[2]
                ) * self.border_progress.value
            ),
        )

        pygame.draw.rect(
            surface,
            border_color,
            animated_rect,
            width=2,
            border_radius=16
        )

        title_surface = self.font.render(
            self.text,
            True,
            WHITE if self.enabled else TEXT_SECONDARY
        )

        if self.subtitle:
            title_rect = title_surface.get_rect(
                center=(
                    animated_rect.centerx,
                    animated_rect.centery - 10
                )
            )
        else:
            title_rect = title_surface.get_rect(
                center=animated_rect.center
            )

        surface.blit(title_surface, title_rect)

        if self.subtitle:
            subtitle_font = pygame.font.SysFont(
                "segoeui",
                14
            )

            subtitle_surface = subtitle_font.render(
                self.subtitle,
                True,
                TEXT_SECONDARY
            )

            subtitle_rect = subtitle_surface.get_rect(
                center=(
                    animated_rect.centerx,
                    animated_rect.centery + 18
                )
            )

            surface.blit(
                subtitle_surface,
                subtitle_rect
            )

    def handle_event(self, event):
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if (
                event.button == 1
                and self.base_rect.collidepoint(
                    event.pos
                )
            ):
                self.pressed = True

        if event.type == pygame.MOUSEBUTTONUP:
            was_pressed = self.pressed
            self.pressed = False

            if (
                event.button == 1
                and was_pressed
                and self.base_rect.collidepoint(
                    event.pos
                )
            ):
                return True

        return False