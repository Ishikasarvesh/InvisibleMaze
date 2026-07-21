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
            AnimatedValue(0)
        ]

        # Stack buttons vertically on the left
        btn_x = 80
        btn_w = 280
        btn_h = 50
        start_y = 150
        gap = 62

        self.continue_button = AnimatedButton(
            btn_x, start_y, btn_w, btn_h,
            "Continue", self.fonts["body"],
            subtitle="Resume active progression"
        )
        self.select_world_button = AnimatedButton(
            btn_x, start_y + gap, btn_w, btn_h,
            "Select World", self.fonts["body"],
            subtitle="Journey through 6 worlds"
        )
        self.customize_button = AnimatedButton(
            btn_x, start_y + gap * 2, btn_w, btn_h,
            "Customize Character", self.fonts["body"],
            subtitle="Equip custom skins"
        )
        self.settings_button = AnimatedButton(
            btn_x, start_y + gap * 3, btn_w, btn_h,
            "Settings", self.fonts["body"],
            subtitle="Configure rules & sound"
        )
        self.how_to_play_button = AnimatedButton(
            btn_x, start_y + gap * 4, btn_w, btn_h,
            "How to Play", self.fonts["body"],
            subtitle="Check game instructions"
        )
        self.quit_button = AnimatedButton(
            btn_x, start_y + gap * 5, btn_w, btn_h,
            "Quit Game", self.fonts["body"],
            subtitle="Exit the application"
        )

        self.buttons = [
            self.continue_button,
            self.select_world_button,
            self.customize_button,
            self.settings_button,
            self.how_to_play_button,
            self.quit_button,
        ]

        self.title_offset.set_target(0)
        self.title_alpha.set_target(1)

        self.subtitle_offset.set_target(0)
        self.subtitle_alpha.set_target(1)

        self.save_data = None
        self.selected_world_id = "1"

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

        if self.save_data:
            latest_unlocked = self.save_data.get("unlocked_levels", ["1-1"])[-1]
            self.continue_button.subtitle = f"Resume Level {latest_unlocked}"
        else:
            self.continue_button.subtitle = "No active save progress"

        for button in self.buttons:
            button.update(
                delta_time,
                mouse_position,
            )

    # =====================================================
    # EVENTS
    # =====================================================

    def handle_event(self, event):
        if self.continue_button.handle_event(event):
            return ("continue", None)

        if self.select_world_button.handle_event(event):
            return ("select_world", None)

        if self.customize_button.handle_event(event):
            return ("customize", None)

        if self.settings_button.handle_event(event):
            return ("settings", None)

        if self.how_to_play_button.handle_event(event):
            return ("how_to_play", None)

        if self.quit_button.handle_event(event):
            return ("quit", None)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                return ("continue", None)

            if event.key == pygame.K_w:
                return ("select_world", None)

            if event.key == pygame.K_p:
                return ("customize", None)

            if event.key == pygame.K_s:
                return ("settings", None)

            if event.key == pygame.K_h:
                return ("how_to_play", None)

            if event.key == pygame.K_q:
                return ("quit", None)

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
            distance=5,
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
                    65
                    + self.title_offset.value
                    + floating
                ),
            )
        )

        glow_surface = pygame.Surface(
            (
                title_rect.width + 60,
                title_rect.height + 40,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.ellipse(
            glow_surface,
            (
                255,
                216,
                110,
                24,
            ),
            glow_surface.get_rect(),
        )

        surface.blit(
            glow_surface,
            (
                title_rect.x - 30,
                title_rect.y - 20,
            ),
        )

        surface.blit(
            title_surface,
            title_rect,
        )

        subtitle = (
            "Explore 30 dangerous procedurally generated levels."
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
                        112
                        + self.subtitle_offset.value
                    ),
                )
            )
        )

        surface.blit(
            subtitle_surface,
            subtitle_rect,
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
    def draw(self, surface):
        self.draw_background(surface)

        self.particle_manager.draw_fireflies(
            surface
        )

        self.draw_title(surface)

        for button in self.buttons:
            button.draw(surface)

        # Draw Right Character Preview Area
        px = 700
        py = 370
        preview_r = 50

        # Draw outer circle frame
        from game.settings import PANEL, PANEL_BORDER
        pygame.draw.circle(surface, PANEL, (px, py), 160)
        pygame.draw.circle(surface, PANEL_BORDER, (px, py), 160, width=4)

        # Title
        world_text = "WORLD PROGRESS"
        world_surf = self.fonts["tiny"].render(world_text, True, TEXT_MUTED)
        surface.blit(world_surf, world_surf.get_rect(center=(px, py - 110)))

        # Selected Skin name
        equipped_skin = "Shadow Ninja"
        equipped_accessory = "Scarlet Scarf"
        equipped_colors = ((0, 0, 0), (245, 82, 95))
        
        if self.save_data:
            equipped_skin = self.save_data.get("selected_skin_by_world", {}).get(self.selected_world_id, "Shadow Ninja")
            equipped_accessory = self.save_data.get("selected_accessories_by_world", {}).get(self.selected_world_id, "Scarlet Scarf")
            equipped_colors = self.save_data.get("selected_colors_by_world", {}).get(self.selected_world_id, ((0, 0, 0), (245, 82, 95)))

        skin_surf = self.fonts["subheading"].render(equipped_skin, True, WHITE)
        surface.blit(skin_surf, skin_surf.get_rect(center=(px, py + 110)))

        # Draw preview character programmatically doing an idle bounce
        bounce = math.sin(self.animation_time * 5.0) * 4
        from game.player_customization import CustomizationManager
        CustomizationManager.draw_player(
            surface=surface,
            cx=px,
            cy=py + int(bounce),
            radius=preview_r,
            player=None,
            skin_name=equipped_skin,
            primary_color=equipped_colors[0],
            secondary_color=equipped_colors[1],
            accessory_name=equipped_accessory,
        )

        self.draw_footer(surface)