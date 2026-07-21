import pygame
import math
from game.player_customization import CustomizationManager
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, BLUE, GREEN, RED, PANEL, PANEL_BORDER, TEXT_MUTED

class CustomizationScreen:
    """
    Renders player skins, custom colors, accessory items,
    unlock guidelines, and interactive preview animations.
    """

    def __init__(self, fonts, save_data, world_id):
        self.fonts = fonts
        self.save_data = save_data
        self.world_id = str(world_id)
        
        # Selected list of skins for this world
        self.skins = CustomizationManager.get_skins_for_world(self.world_id)
        self.selected_skin_index = 0
        
        self.accessories = list(CustomizationManager.ACCESSORIES.keys())
        self.selected_accessory_index = 0

        # Colors options
        self.colors_palette = [
            # Primary, Secondary
            ((245, 82, 95), (255, 255, 255)), # Red / White
            ((89, 145, 255), (255, 255, 255)), # Blue / White
            ((69, 230, 154), (255, 255, 255)), # Green / White
            ((255, 215, 0), (0, 0, 0)),        # Gold / Black
            ((255, 100, 200), (255, 255, 255)), # Pink / White
            ((15, 230, 180), (20, 20, 30)),     # Neon / Dark
        ]
        self.selected_color_index = 0
        
        self.focus_column = 0 # 0: Skins, 1: Accessories, 2: Colors
        self.animation_time = 0.0

        # Load currently equipped from save data
        equipped_skin = self.save_data.get("selected_skin_by_world", {}).get(self.world_id)
        if equipped_skin in self.skins:
            self.selected_skin_index = self.skins.index(equipped_skin)

        equipped_accessory = self.save_data.get("selected_accessories_by_world", {}).get(self.world_id)
        if equipped_accessory in self.accessories:
            self.selected_accessory_index = self.accessories.index(equipped_accessory)

        equipped_colors = self.save_data.get("selected_colors_by_world", {}).get(self.world_id)
        if equipped_colors:
            equipped_tuple = (tuple(equipped_colors[0]), tuple(equipped_colors[1]))
            for idx, pal in enumerate(self.colors_palette):
                pal_tup = (tuple(pal[0]), tuple(pal[1]))
                if pal_tup == equipped_tuple:
                    self.selected_color_index = idx
                    break

    def update(self, delta_time):
        self.animation_time += delta_time

    def handle_event(self, event):
        """
        Supports keyboard focus selectors and mouse clicks.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.focus_column = (self.focus_column - 1) % 3
                return None
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.focus_column = (self.focus_column + 1) % 3
                return None
            elif event.key in (pygame.K_UP, pygame.K_w):
                if self.focus_column == 0:
                    self.selected_skin_index = (self.selected_skin_index - 1) % len(self.skins)
                elif self.focus_column == 1:
                    self.selected_accessory_index = (self.selected_accessory_index - 1) % len(self.accessories)
                elif self.focus_column == 2:
                    self.selected_color_index = (self.selected_color_index - 1) % len(self.colors_palette)
                return None
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.focus_column == 0:
                    self.selected_skin_index = (self.selected_skin_index + 1) % len(self.skins)
                elif self.focus_column == 1:
                    self.selected_accessory_index = (self.selected_accessory_index + 1) % len(self.accessories)
                elif self.focus_column == 2:
                    self.selected_color_index = (self.selected_color_index + 1) % len(self.colors_palette)
                return None
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.equip_current_selection()
            elif event.key == pygame.K_ESCAPE:
                return ("back", None)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # Back Button
                back_rect = pygame.Rect(40, 40, 100, 40)
                if back_rect.collidepoint(mouse_pos):
                    return ("back", None)

                # Save / Equip Button
                equip_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 130, 200, 46)
                if equip_rect.collidepoint(mouse_pos):
                    return self.equip_current_selection()

                # Check column clicks
                # Skins column items
                for i in range(len(self.skins)):
                    rect = pygame.Rect(60, 150 + i * 45, 200, 36)
                    if rect.collidepoint(mouse_pos):
                        self.focus_column = 0
                        self.selected_skin_index = i
                        return None
                
                # Accessories column items
                for i in range(len(self.accessories)):
                    rect = pygame.Rect(SCREEN_WIDTH - 260, 150 + i * 45, 200, 36)
                    if rect.collidepoint(mouse_pos):
                        self.focus_column = 1
                        self.selected_accessory_index = i
                        return None

                # Colors column items
                for i in range(len(self.colors_palette)):
                    rect = pygame.Rect(SCREEN_WIDTH - 260, 400 + i * 35, 200, 30)
                    if rect.collidepoint(mouse_pos):
                        self.focus_column = 2
                        self.selected_color_index = i
                        return None

        return None

    def is_skin_unlocked(self, skin_name):
        return skin_name in self.save_data.get("unlocked_skins", [])

    def is_accessory_unlocked(self, acc_name):
        return acc_name in self.save_data.get("unlocked_cosmetics", [])

    def equip_current_selection(self):
        skin_name = self.skins[self.selected_skin_index]
        acc_name = self.accessories[self.selected_accessory_index]
        colors = self.colors_palette[self.selected_color_index]

        # Check unlocks
        if not self.is_skin_unlocked(skin_name):
            return ("error_lock", f"Locked: {CustomizationManager.get_unlock_info(skin_name)}")
        if not self.is_accessory_unlocked(acc_name):
            return ("error_lock", f"Locked: {CustomizationManager.get_unlock_info(acc_name)}")

        # Update save data dictionary
        if "selected_skin_by_world" not in self.save_data:
            self.save_data["selected_skin_by_world"] = {}
        if "selected_accessories_by_world" not in self.save_data:
            self.save_data["selected_accessories_by_world"] = {}
        if "selected_colors_by_world" not in self.save_data:
            self.save_data["selected_colors_by_world"] = {}

        self.save_data["selected_skin_by_world"][self.world_id] = skin_name
        self.save_data["selected_accessories_by_world"][self.world_id] = acc_name
        self.save_data["selected_colors_by_world"][self.world_id] = list(colors)

        return ("equipped", (skin_name, acc_name, colors))

    def draw(self, surface):
        surface.fill(PANEL)

        # Draw Title
        title_surf = self.fonts["heading"].render("CUSTOMIZE CHARACTER", True, WHITE)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 70)))

        # Back Button
        pygame.draw.rect(surface, PANEL_BORDER, (40, 40, 100, 40), border_radius=8)
        back_text = self.fonts["body"].render("Back", True, WHITE)
        surface.blit(back_text, back_text.get_rect(center=(90, 60)))

        # --- 1. COLUMN: SKINS (Left side) ---
        skins_label = self.fonts["subheading"].render("SKINS", True, BLUE)
        surface.blit(skins_label, (60, 115))

        for i, skin in enumerate(self.skins):
            is_sel = (i == self.selected_skin_index)
            is_col_focus = (self.focus_column == 0)
            rect = pygame.Rect(60, 150 + i * 45, 200, 36)
            
            # Card background
            bg_color = (25, 25, 35) if is_sel else PANEL
            pygame.draw.rect(surface, bg_color, rect, border_radius=6)
            
            border_color = YELLOW if (is_sel and is_col_focus) else (PANEL_BORDER if is_sel else (40, 40, 50))
            pygame.draw.rect(surface, border_color, rect, width=2, border_radius=6)

            # Draw name
            unlocked = self.is_skin_unlocked(skin)
            text_color = WHITE if unlocked else TEXT_MUTED
            skin_surf = self.fonts["body"].render(skin, True, text_color)
            surface.blit(skin_surf, (rect.left + 10, rect.top + 6))
            
            if not unlocked:
                # mini lock icon
                pygame.draw.rect(surface, RED, (rect.right - 22, rect.top + 12, 10, 8))
                pygame.draw.circle(surface, RED, (rect.right - 17, rect.top + 12), 4, width=1)

        # --- 2. COLUMN: ACCESSORIES (Right side top) ---
        acc_label = self.fonts["subheading"].render("ACCESSORIES", True, BLUE)
        surface.blit(acc_label, (SCREEN_WIDTH - 260, 115))

        for i, acc in enumerate(self.accessories):
            is_sel = (i == self.selected_accessory_index)
            is_col_focus = (self.focus_column == 1)
            rect = pygame.Rect(SCREEN_WIDTH - 260, 150 + i * 45, 200, 36)

            bg_color = (25, 25, 35) if is_sel else PANEL
            pygame.draw.rect(surface, bg_color, rect, border_radius=6)

            border_color = YELLOW if (is_sel and is_col_focus) else (PANEL_BORDER if is_sel else (40, 40, 50))
            pygame.draw.rect(surface, border_color, rect, width=2, border_radius=6)

            unlocked = self.is_accessory_unlocked(acc)
            text_color = WHITE if unlocked else TEXT_MUTED
            acc_surf = self.fonts["body"].render(acc, True, text_color)
            surface.blit(acc_surf, (rect.left + 10, rect.top + 6))

            if not unlocked:
                pygame.draw.rect(surface, RED, (rect.right - 22, rect.top + 12, 10, 8))
                pygame.draw.circle(surface, RED, (rect.right - 17, rect.top + 12), 4, width=1)

        # --- 3. COLUMN: COLOR SCHEMES (Right side bottom) ---
        col_label = self.fonts["subheading"].render("COLOR SCHEMES", True, BLUE)
        surface.blit(col_label, (SCREEN_WIDTH - 260, 360))

        for i, colors in enumerate(self.colors_palette):
            is_sel = (i == self.selected_color_index)
            is_col_focus = (self.focus_column == 2)
            rect = pygame.Rect(SCREEN_WIDTH - 260, 400 + i * 35, 200, 30)

            border_color = YELLOW if (is_sel and is_col_focus) else (PANEL_BORDER if is_sel else (40, 40, 50))
            pygame.draw.rect(surface, border_color, rect, width=2, border_radius=4)

            # Draw two color patches inside
            pygame.draw.rect(surface, colors[0], (rect.left + 15, rect.top + 5, 40, 20), border_radius=3)
            pygame.draw.rect(surface, colors[1], (rect.left + 65, rect.top + 5, 40, 20), border_radius=3)

        # --- 4. CENTER PREVIEW AREA ---
        px = SCREEN_WIDTH // 2
        py = SCREEN_HEIGHT // 2 - 20
        preview_r = 45

        # Glowing halo outline
        pulse = (math.sin(self.animation_time * 5.0) + 1.0) / 2.0
        glow_r = int(preview_r + 15 + pulse * 6)
        pygame.draw.circle(surface, (255, 255, 255, 12), (px, py), glow_r)

        # Draw live player character preview in center
        current_skin = self.skins[self.selected_skin_index]
        current_accessory = self.accessories[self.selected_accessory_index]
        current_colors = self.colors_palette[self.selected_color_index]

        # Draw character preview
        CustomizationManager.draw_player(
            surface=surface,
            cx=px,
            cy=py,
            radius=preview_r,
            player=None,
            skin_name=current_skin,
            primary_color=current_colors[0],
            secondary_color=current_colors[1],
            accessory_name=current_accessory,
        )

        # Unlock requirement text card (below preview)
        if self.focus_column == 0:
            focus_item = self.skins[self.selected_skin_index]
            unlocked = self.is_skin_unlocked(focus_item)
            info_text = f"Unlock: {CustomizationManager.get_unlock_info(focus_item)}"
        elif self.focus_column == 1:
            focus_item = self.accessories[self.selected_accessory_index]
            unlocked = self.is_accessory_unlocked(focus_item)
            info_text = f"Unlock: {CustomizationManager.get_unlock_info(focus_item)}"
        else:
            unlocked = True
            info_text = "Unlock: Color Schemes unlocked by default"

        info_rect = pygame.Rect(SCREEN_WIDTH // 2 - 160, py + 75, 320, 40)
        pygame.draw.rect(surface, (25, 25, 30), info_rect, border_radius=6)
        pygame.draw.rect(surface, PANEL_BORDER, info_rect, width=1, border_radius=6)

        info_color = GREEN if unlocked else RED
        info_surf = self.fonts["tiny"].render(info_text, True, info_color)
        surface.blit(info_surf, info_surf.get_rect(center=info_rect.center))

        # --- Save/Equip Button ---
        equip_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 130, 200, 46)
        pygame.draw.rect(surface, PANEL_BORDER, equip_rect, border_radius=8)
        
        btn_text = "EQUIP CHARACTER" if unlocked else "LOCKED"
        btn_color = WHITE if unlocked else TEXT_MUTED
        btn_surf = self.fonts["body"].render(btn_text, True, btn_color)
        surface.blit(btn_surf, btn_surf.get_rect(center=equip_rect.center))
