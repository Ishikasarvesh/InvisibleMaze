import pygame

from game.animations import AnimatedValue, floating_offset, pulse
from game.settings import (
    BACKGROUND,
    BLUE,
    GREEN,
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


class ResultScreen:
    """
    Displays the player's result after reaching the exit.
    """

    def __init__(
        self,
        fonts,
        particle_manager,
    ):
        self.fonts = fonts
        self.particle_manager = particle_manager

        self.animation_time = 0

        self.difficulty = "Easy"
        self.moves = 0
        self.elapsed_seconds = 0
        self.battery = 0
        self.score = 0

        self.displayed_score = AnimatedValue(0)
        self.panel_progress = AnimatedValue(0)
        self.title_progress = AnimatedValue(0)

        panel_width = 660
        panel_height = 580

        self.panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - panel_width // 2,
            SCREEN_HEIGHT // 2 - panel_height // 2,
            panel_width,
            panel_height,
        )

        button_width = 135
        button_height = 50
        gap = 12
        total_width = button_width * 4 + gap * 3
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        button_y = self.panel_rect.bottom - 75

        self.next_level_button = AnimatedButton(
            start_x,
            button_y,
            button_width,
            button_height,
            "Next Level",
            self.fonts["tiny"],
            subtitle=""
        )

        self.replay_button = AnimatedButton(
            start_x + button_width + gap,
            button_y,
            button_width,
            button_height,
            "Replay",
            self.fonts["tiny"],
            subtitle=""
        )

        self.level_select_button = AnimatedButton(
            start_x + (button_width + gap) * 2,
            button_y,
            button_width,
            button_height,
            "Level Select",
            self.fonts["tiny"],
            subtitle=""
        )

        self.menu_button = AnimatedButton(
            start_x + (button_width + gap) * 3,
            button_y,
            button_width,
            button_height,
            "Main Menu",
            self.fonts["tiny"],
            subtitle=""
        )

        self.buttons = [
            self.next_level_button,
            self.replay_button,
            self.level_select_button,
            self.menu_button,
        ]

        self.has_next_level = False
        self.stars_earned = 0
        self.new_record = False
        self.unlocked_rewards = None
        self.level_id = None

    # =====================================================
    # OPEN RESULT
    # =====================================================

    def open(
        self,
        difficulty,
        moves,
        elapsed_seconds,
        battery,
        score,
        level_id=None,
        has_next_level=False,
        stars_earned=0,
        new_record=False,
        unlocked_rewards=None,
    ):
        """
        Stores final values and restarts the animations.
        """
        self.difficulty = difficulty
        self.moves = moves
        self.elapsed_seconds = elapsed_seconds
        self.battery = battery
        self.score = score
        self.level_id = level_id
        self.has_next_level = has_next_level
        self.stars_earned = stars_earned
        self.new_record = new_record
        self.unlocked_rewards = unlocked_rewards

        self.animation_time = 0

        self.displayed_score.snap(0)
        self.displayed_score.set_target(score)

        self.panel_progress.snap(0)
        self.panel_progress.set_target(1)

        self.title_progress.snap(0)
        self.title_progress.set_target(1)

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, delta_time):
        """
        Updates panel scales, final score counters, and button animations.
        """
        self.animation_time += delta_time

        mouse_position = pygame.mouse.get_pos()

        self.panel_progress.update(
            delta_time,
            speed=4.5,
        )

        self.title_progress.update(
            delta_time,
            speed=3.5,
        )

        self.displayed_score.update(
            delta_time,
            speed=2.2,
        )

        # Show next level button only if available
        for btn in self.buttons:
            if btn == self.next_level_button and not self.has_next_level:
                continue
            btn.update(delta_time, mouse_position)

    # =====================================================
    # EVENTS
    # =====================================================

    def handle_event(self, event):
        """
        Handles result-screen controls.
        """
        if self.has_next_level and self.next_level_button.handle_event(event):
            return "next_level"

        if self.replay_button.handle_event(event):
            return "replay"

        if self.level_select_button.handle_event(event):
            return "level_select"

        if self.menu_button.handle_event(event):
            return "menu"

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "next_level" if self.has_next_level else "level_select"

            if event.key == pygame.K_r:
                return "replay"

            if event.key in (
                pygame.K_ESCAPE,
                pygame.K_m,
            ):
                return "menu"

        return None

    # =====================================================
    # BACKGROUND
    # =====================================================

    def draw_background(self, surface):
        """
        Draws a dark background with animated glows.
        """

        surface.fill(BACKGROUND)

        glow_surface = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        glow_radius = int(
            pulse(
                self.animation_time,
                speed=1.5,
                minimum=190,
                maximum=245,
            )
        )

        pygame.draw.circle(
            glow_surface,
            (
                GREEN[0],
                GREEN[1],
                GREEN[2],
                25,
            ),
            (
                SCREEN_WIDTH // 2,
                160,
            ),
            glow_radius,
        )

        pygame.draw.circle(
            glow_surface,
            (
                BLUE[0],
                BLUE[1],
                BLUE[2],
                12,
            ),
            (
                180,
                SCREEN_HEIGHT - 130,
            ),
            230,
        )

        pygame.draw.circle(
            glow_surface,
            (
                YELLOW[0],
                YELLOW[1],
                YELLOW[2],
                12,
            ),
            (
                SCREEN_WIDTH - 180,
                SCREEN_HEIGHT - 160,
            ),
            210,
        )

        surface.blit(
            glow_surface,
            (0, 0),
        )

    # =====================================================
    # PANEL
    # =====================================================

    def get_animated_panel_rect(self):
        """
        Returns the result panel with scale animation.
        """

        progress = max(
            0,
            min(
                1,
                self.panel_progress.value,
            ),
        )

        scale = (
            0.82
            + progress * 0.18
        )

        animated_width = max(
            1,
            int(
                self.panel_rect.width
                * scale
            ),
        )

        animated_height = max(
            1,
            int(
                self.panel_rect.height
                * scale
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
        Draws the central result panel.
        """

        animated_rect = (
            self.get_animated_panel_rect()
        )

        shadow_rect = animated_rect.copy()
        shadow_rect.y += 12

        pygame.draw.rect(
            surface,
            (
                0,
                0,
                0,
            ),
            shadow_rect,
            border_radius=30,
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
            border_radius=30,
        )

        pygame.draw.rect(
            panel_surface,
            PANEL_BORDER,
            panel_surface.get_rect(),
            width=2,
            border_radius=30,
        )

        surface.blit(
            panel_surface,
            animated_rect,
        )

    # =====================================================
    # TROPHY
    # =====================================================

    def draw_trophy(self, surface):
        """
        Draws a simple animated trophy icon.
        """

        center_x = SCREEN_WIDTH // 2

        float_y = floating_offset(
            self.animation_time,
            speed=2,
            distance=7,
        )

        center_y = int(
            self.panel_rect.y
            + 78
            + float_y
        )

        glow_radius = int(
            pulse(
                self.animation_time,
                speed=2.5,
                minimum=48,
                maximum=58,
            )
        )

        glow_surface = pygame.Surface(
            (
                glow_radius * 4,
                glow_radius * 4,
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
                YELLOW[0],
                YELLOW[1],
                YELLOW[2],
                35,
            ),
            glow_center,
            glow_radius,
        )

        surface.blit(
            glow_surface,
            (
                center_x
                - glow_surface.get_width() // 2,
                center_y
                - glow_surface.get_height() // 2,
            ),
        )

        cup_rect = pygame.Rect(
            center_x - 25,
            center_y - 25,
            50,
            45,
        )

        pygame.draw.rect(
            surface,
            YELLOW,
            cup_rect,
            border_radius=10,
        )

        left_handle = pygame.Rect(
            cup_rect.left - 17,
            cup_rect.top + 7,
            25,
            25,
        )

        right_handle = pygame.Rect(
            cup_rect.right - 8,
            cup_rect.top + 7,
            25,
            25,
        )

        pygame.draw.arc(
            surface,
            YELLOW,
            left_handle,
            1.4,
            4.9,
            width=6,
        )

        pygame.draw.arc(
            surface,
            YELLOW,
            right_handle,
            -1.8,
            1.8,
            width=6,
        )

        stem_rect = pygame.Rect(
            center_x - 5,
            cup_rect.bottom,
            10,
            17,
        )

        base_rect = pygame.Rect(
            center_x - 24,
            stem_rect.bottom - 1,
            48,
            9,
        )

        pygame.draw.rect(
            surface,
            YELLOW,
            stem_rect,
            border_radius=3,
        )

        pygame.draw.rect(
            surface,
            YELLOW,
            base_rect,
            border_radius=4,
        )

    # =====================================================
    # TITLE AND SCORE
    # =====================================================

    def draw_title(self, surface):
        """
        Draws the victory title.
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

        display_title = "LEVEL COMPLETE!" if self.level_id else "MAZE ESCAPED!"
        title_surface = self.fonts["heading"].render(display_title, True, WHITE)
        title_surface.set_alpha(alpha)

        surface.blit(
            title_surface,
            title_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    self.panel_rect.y + 155,
                )
            ),
        )

        sub_text = "You successfully solved the maze and found the exit!"
        if self.level_id:
            sub_text = "You unlocked the next challenge."

        subtitle_surface = self.fonts["small"].render(sub_text, True, TEXT_SECONDARY)
        subtitle_surface.set_alpha(alpha)

        surface.blit(
            subtitle_surface,
            subtitle_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    self.panel_rect.y + 196,
                )
            ),
        )

        # Draw stars
        stars_y = self.panel_rect.y + 245
        for i in range(3):
            star_x = SCREEN_WIDTH // 2 + (i - 1) * 50
            color = YELLOW if i < self.stars_earned else (70, 70, 80)
            star_surf = self.fonts["heading"].render("★", True, color)
            star_surf.set_alpha(alpha)
            surface.blit(star_surf, star_surf.get_rect(center=(star_x, stars_y)))

    def draw_score(self, surface):
        """
        Draws the animated final score.
        """
        score_label = self.fonts[
            "tiny"
        ].render(
            "FINAL SCORE",
            True,
            TEXT_MUTED,
        )

        surface.blit(
            score_label,
            score_label.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    self.panel_rect.y + 295,
                )
            ),
        )

        score_surface = self.fonts[
            "title"
        ].render(
            str(
                int(
                    self.displayed_score.value
                )
            ),
            True,
            YELLOW,
        )

        surface.blit(
            score_surface,
            score_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    self.panel_rect.y + 338,
                )
            ),
        )

    # =====================================================
    # STAT CARDS
    # =====================================================

    def draw_stat_card(
        self,
        surface,
        rect,
        label,
        value,
        accent_color,
    ):
        """
        Draws one game-statistics card.
        """

        pygame.draw.rect(
            surface,
            (
                26,
                33,
                50,
            ),
            rect,
            border_radius=16,
        )

        pygame.draw.rect(
            surface,
            (
                accent_color[0],
                accent_color[1],
                accent_color[2],
            ),
            rect,
            width=1,
            border_radius=16,
        )

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
            label_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.y + 23,
                )
            ),
        )

        surface.blit(
            value_surface,
            value_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.y + 57,
                )
            ),
        )

    def draw_statistics(self, surface):
        """
        Draws difficulty, moves, time and battery.
        """

        card_width = 132
        card_height = 82
        card_gap = 14

        total_width = (
            card_width * 4
            + card_gap * 3
        )

        start_x = (
            SCREEN_WIDTH - total_width
        ) // 2

        card_y = self.panel_rect.y + 400

        cards = [
            (
                "Difficulty",
                self.difficulty,
                BLUE,
            ),
            (
                "Moves",
                str(self.moves),
                WHITE,
            ),
            (
                "Time",
                f"{self.elapsed_seconds}s",
                GREEN,
            ),
            (
                "Battery",
                f"{int(self.battery)}%",
                ORANGE,
            ),
        ]

        for index, (
            label,
            value,
            color,
        ) in enumerate(cards):
            card_rect = pygame.Rect(
                start_x
                + index
                * (
                    card_width
                    + card_gap
                ),
                card_y,
                card_width,
                card_height,
            )

            self.draw_stat_card(
                surface,
                card_rect,
                label,
                value,
                color,
            )

    # =====================================================
    # FOOTER
    # =====================================================

    def draw_footer(self, surface):
        """
        Draws result-screen keyboard controls.
        """

        hint_surface = self.fonts[
            "tiny"
        ].render(
            "Enter / R: Play Again    M / Esc: Main Menu",
            True,
            TEXT_MUTED,
        )

        surface.blit(
            hint_surface,
            hint_surface.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    SCREEN_HEIGHT - 28,
                )
            ),
        )

    # =====================================================
    # DRAW
    # =====================================================

    def draw(self, surface):
        """
        Draws the complete result screen.
        """
        self.draw_background(surface)

        self.particle_manager.draw_fireflies(
            surface
        )

        self.particle_manager.draw_particles(
            surface
        )

        self.draw_panel(surface)
        self.draw_trophy(surface)
        self.draw_title(surface)
        self.draw_score(surface)
        self.draw_statistics(surface)

        # Draw dynamic notification alert
        if self.new_record or self.unlocked_rewards:
            y_pos = self.panel_rect.y + 490
            text = "NEW BEST RECORD!" if self.new_record else f"UNLOCKED: {self.unlocked_rewards}!"
            color = YELLOW if self.new_record else GREEN
            notify_surf = self.fonts["body"].render(text, True, color)
            surface.blit(notify_surf, notify_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos)))

        for button in self.buttons:
            if button == self.next_level_button and not self.has_next_level:
                continue
            button.draw(surface)

        self.draw_footer(surface)