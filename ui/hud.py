import pygame

from game.animations import AnimatedValue, pulse
from game.settings import (
    BLUE,
    GREEN,
    HUD_HEIGHT,
    ORANGE,
    PANEL,
    PANEL_BORDER,
    RED,
    SCREEN_WIDTH,
    TEXT_MUTED,
    TEXT_SECONDARY,
    WHITE,
    YELLOW,
)


class HUD:
    """
    Displays game information such as battery,
    timer, moves, difficulty and notifications.
    """

    def __init__(self, fonts):
        self.fonts = fonts

        self.displayed_battery = AnimatedValue(100)
        self.displayed_score = AnimatedValue(0)

        self.notification_text = ""
        self.notification_timer = 0
        self.notification_duration = 2.2

        self.animation_time = 0

    # =====================================================
    # UPDATE
    # =====================================================

    def update(
        self,
        delta_time,
        battery,
        score,
    ):
        self.animation_time += delta_time

        self.displayed_battery.set_target(
            battery
        )

        self.displayed_score.set_target(
            score
        )

        self.displayed_battery.update(
            delta_time,
            speed=7,
        )

        self.displayed_score.update(
            delta_time,
            speed=7,
        )

        if self.notification_timer > 0:
            self.notification_timer -= delta_time

            if self.notification_timer <= 0:
                self.notification_text = ""

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    def show_notification(
        self,
        text,
        duration=2.2,
    ):
        self.notification_text = text
        self.notification_duration = duration
        self.notification_timer = duration

    # =====================================================
    # COLORS
    # =====================================================

    def get_battery_color(self):
        battery = self.displayed_battery.value

        if battery > 60:
            return GREEN

        if battery > 30:
            return YELLOW

        if battery > 15:
            return ORANGE

        return RED

    # =====================================================
    # MAIN HUD PANEL
    # =====================================================

    def draw_panel(self, surface):
        panel_rect = pygame.Rect(
            20,
            14,
            SCREEN_WIDTH - 40,
            HUD_HEIGHT - 22,
        )

        shadow_rect = panel_rect.copy()
        shadow_rect.y += 5

        pygame.draw.rect(
            surface,
            (
                0,
                0,
                0,
            ),
            shadow_rect,
            border_radius=18,
        )

        pygame.draw.rect(
            surface,
            PANEL,
            panel_rect,
            border_radius=18,
        )

        pygame.draw.rect(
            surface,
            PANEL_BORDER,
            panel_rect,
            width=1,
            border_radius=18,
        )

        return panel_rect

    # =====================================================
    # INFO BLOCK
    # =====================================================

    def draw_info_item(
        self,
        surface,
        x,
        label,
        value,
        accent_color=WHITE,
    ):
        label_surface = self.fonts[
            "tiny"
        ].render(
            label.upper(),
            True,
            TEXT_MUTED,
        )

        value_surface = self.fonts[
            "body"
        ].render(
            value,
            True,
            accent_color,
        )

        surface.blit(
            label_surface,
            (
                x,
                29,
            ),
        )

        surface.blit(
            value_surface,
            (
                x,
                46,
            ),
        )

    # =====================================================
    # BATTERY
    # =====================================================

    def draw_battery(
        self,
        surface,
        x,
        width,
    ):
        battery_value = max(
            0,
            min(
                100,
                self.displayed_battery.value,
            ),
        )

        label_surface = self.fonts[
            "tiny"
        ].render(
            "TORCH",
            True,
            TEXT_MUTED,
        )

        percentage_surface = self.fonts[
            "small"
        ].render(
            f"{int(battery_value)}%",
            True,
            self.get_battery_color(),
        )

        surface.blit(
            label_surface,
            (
                x,
                25,
            ),
        )

        surface.blit(
            percentage_surface,
            (
                x + width
                - percentage_surface.get_width(),
                25,
            ),
        )

        bar_rect = pygame.Rect(
            x,
            51,
            width,
            12,
        )

        pygame.draw.rect(
            surface,
            (
                38,
                45,
                62,
            ),
            bar_rect,
            border_radius=6,
        )

        fill_width = int(
            bar_rect.width
            * battery_value
            / 100
        )

        if fill_width > 0:
            fill_rect = pygame.Rect(
                bar_rect.x,
                bar_rect.y,
                fill_width,
                bar_rect.height,
            )

            pygame.draw.rect(
                surface,
                self.get_battery_color(),
                fill_rect,
                border_radius=6,
            )

        shine_rect = pygame.Rect(
            bar_rect.x + 2,
            bar_rect.y + 2,
            max(
                0,
                fill_width - 4,
            ),
            2,
        )

        if shine_rect.width > 0:
            pygame.draw.rect(
                surface,
                (
                    255,
                    255,
                    255,
                ),
                shine_rect,
                border_radius=2,
            )

    # =====================================================
    # LOW BATTERY WARNING
    # =====================================================

    def draw_low_battery_warning(
        self,
        surface,
    ):
        battery = self.displayed_battery.value

        if battery > 20:
            return

        warning_alpha = int(
            pulse(
                self.animation_time,
                speed=5,
                minimum=90,
                maximum=255,
            )
        )

        warning_surface = self.fonts[
            "small"
        ].render(
            "LOW TORCH ENERGY",
            True,
            RED,
        )

        warning_surface.set_alpha(
            warning_alpha
        )

        warning_rect = (
            warning_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    HUD_HEIGHT + 12,
                )
            )
        )

        surface.blit(
            warning_surface,
            warning_rect,
        )

    # =====================================================
    # NOTIFICATION
    # =====================================================

    def draw_notification(self, surface):
        if not self.notification_text:
            return

        life_ratio = max(
            0,
            min(
                1,
                self.notification_timer
                / self.notification_duration,
            ),
        )

        alpha = int(
            255
            * min(
                1,
                life_ratio * 2,
            )
        )

        offset_y = int(
            (1 - life_ratio) * -12
        )

        text_surface = self.fonts[
            "small"
        ].render(
            self.notification_text,
            True,
            WHITE,
        )

        padding_x = 24
        padding_y = 12

        background_rect = pygame.Rect(
            0,
            0,
            text_surface.get_width()
            + padding_x * 2,
            text_surface.get_height()
            + padding_y * 2,
        )

        background_rect.center = (
            SCREEN_WIDTH // 2,
            HUD_HEIGHT + 48 + offset_y,
        )

        notification_surface = pygame.Surface(
            (
                background_rect.width,
                background_rect.height,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.rect(
            notification_surface,
            (
                20,
                29,
                48,
                int(225 * life_ratio),
            ),
            notification_surface.get_rect(),
            border_radius=16,
        )

        pygame.draw.rect(
            notification_surface,
            (
                BLUE[0],
                BLUE[1],
                BLUE[2],
                int(160 * life_ratio),
            ),
            notification_surface.get_rect(),
            width=1,
            border_radius=16,
        )

        text_surface.set_alpha(alpha)

        notification_surface.blit(
            text_surface,
            text_surface.get_rect(
                center=(
                    background_rect.width // 2,
                    background_rect.height // 2,
                )
            ),
        )

        surface.blit(
            notification_surface,
            background_rect,
        )

    # =====================================================
    # CONTROL HINT
    # =====================================================

    def draw_control_hint(self, surface):
        hint = (
            "WASD / Arrows: Move   "
            "P: Pause   "
            "R: Restart   "
            "M: Menu"
        )

        hint_surface = self.fonts[
            "tiny"
        ].render(
            hint,
            True,
            TEXT_SECONDARY,
        )

        surface.blit(
            hint_surface,
            hint_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    surface.get_height() - 22,
                )
            ),
        )

    # =====================================================
    # DRAW
    # =====================================================

    def draw_active_powerups(self, surface, active_powerups):
        import math
        if not active_powerups:
            return

        text_parts = []
        for k, v in active_powerups.items():
            if v > 0:
                icon = ""
                if k == "Speed": icon = "⚡ Speed"
                elif k == "Ghost": icon = "👻 Ghost"
                elif k == "Torch": icon = "🔦 Torch"
                elif k == "Freeze": icon = "❄️ Freeze"
                else: icon = k
                text_parts.append(f"{icon} {int(math.ceil(v))}s")

        if not text_parts:
            return

        text_str = "    ".join(text_parts)
        text_surface = self.fonts["small"].render(text_str, True, YELLOW)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, surface.get_height() - 50))

        padding_x = 16
        padding_y = 6
        bg_rect = pygame.Rect(
            text_rect.x - padding_x,
            text_rect.y - padding_y,
            text_rect.width + padding_x * 2,
            text_rect.height + padding_y * 2
        )
        pygame.draw.rect(surface, PANEL, bg_rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER, bg_rect, width=1, border_radius=10)

        surface.blit(text_surface, text_rect)

    def draw(
        self,
        surface,
        difficulty,
        moves,
        elapsed_seconds,
        battery,
        score,
        remaining_batteries,
        active_powerups=None,
    ):
        self.draw_panel(surface)

        if active_powerups:
            self.draw_active_powerups(surface, active_powerups)

        self.draw_info_item(
            surface,
            45,
            "Mode",
            difficulty,
            BLUE,
        )

        self.draw_info_item(
            surface,
            185,
            "Moves",
            str(moves),
            WHITE,
        )

        self.draw_info_item(
            surface,
            300,
            "Time",
            f"{elapsed_seconds}s",
            WHITE,
        )

        self.draw_info_item(
            surface,
            420,
            "Score",
            str(
                int(
                    self.displayed_score.value
                )
            ),
            YELLOW,
        )

        self.draw_info_item(
            surface,
            565,
            "Batteries",
            str(remaining_batteries),
            GREEN,
        )

        self.draw_battery(
            surface,
            x=700,
            width=330,
        )

        self.draw_low_battery_warning(
            surface
        )

        self.draw_notification(surface)

        self.draw_control_hint(surface)