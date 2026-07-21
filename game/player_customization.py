import math
import pygame
from game.settings import WHITE, YELLOW, RED, BLUE, GREEN, ORANGE


class CustomizationManager:
    """
    Manages characters, custom visual drawing routines, accessories,
    and unlock configurations for 30 skins.
    """

    SKINS_BY_WORLD = {
        "1": ["Shadow Ninja", "Crimson Ninja", "Blue Moon Ninja", "White Ronin", "Masked Kunoichi"],
        "2": ["Forest Explorer", "Flower Mage", "Butterfly Knight", "Garden Fairy", "Nature Guardian"],
        "3": ["Ice Warrior", "Snow Scout", "Frost Mage", "Arctic Explorer", "Crystal Knight"],
        "4": ["Ghost Hunter", "Little Witch", "Skeleton Hero", "Cursed Knight", "Victorian Explorer"],
        "5": ["Cyber Ninja", "Neon Hacker", "Battle Android", "Glitch Runner", "Robot Scout"],
        "6": ["Treasure Hunter", "Desert Guardian", "Pharaoh Warrior", "Sand Mage", "Temple Explorer"],
    }

    ACCESSORIES = {
        "Scarlet Scarf": {"color": (245, 82, 95), "style": "scarf"},
        "Fairy Wings": {"color": (195, 140, 255), "style": "wings"},
        "Fur Cloak": {"color": (210, 215, 225), "style": "cloak"},
        "Witch Hat": {"color": (65, 45, 95), "style": "hat"},
        "Neon Visor": {"color": (0, 245, 255), "style": "visor"},
        "Pharaoh Mask": {"color": (255, 215, 0), "style": "crown"},
    }

    @classmethod
    def get_skins_for_world(cls, world_id):
        return cls.SKINS_BY_WORLD.get(str(world_id), [])

    @classmethod
    def draw_player(cls, surface, cx, cy, radius, player, skin_name, primary_color, secondary_color, accessory_name):
        """
        Draws characters using customizable programmatic geometries and smooth animation bobs.
        Supports idle breathing, walking bobbing, eye blinking, ghost transparency, and wall-hit flash.
        """
        ticks = pygame.time.get_ticks()

        # Movement and animation calculations
        is_moving = getattr(player, "is_moving", False) if player is not None else False

        # Calculate bobbing displacement
        if is_moving:
            bob_y = int(abs(math.sin(ticks * 0.016)) * max(2, radius * 0.15))
        else:
            bob_y = int(math.sin(ticks * 0.004) * max(1, radius * 0.08))

        render_cy = cy + bob_y

        # Ghost mode check
        is_ghost = False
        if player is not None:
            powerup_mgr = getattr(player, "powerup_manager", None)
            if powerup_mgr is not None and hasattr(powerup_mgr, "is_active"):
                is_ghost = powerup_mgr.is_active("Ghost")
            else:
                is_ghost = getattr(player, "is_ghost", False)

        # Handle damage hit flash
        hit_val = 0.0
        if player is not None and hasattr(player, "hit_animation"):
            hit_val = getattr(player.hit_animation, "value", 0.0)

        # Target surface for ghost mode / standard mode
        if is_ghost:
            char_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            draw_cx, draw_cy = radius * 2, radius * 2
        else:
            char_surf = surface
            draw_cx, draw_cy = cx, render_cy

        # 1. Draw Accessory behind the body
        cls.draw_accessory(char_surf, draw_cx, draw_cy, radius, accessory_name, is_moving=is_moving)

        # 2. Draw Base Body
        body_color = primary_color
        if hit_val > 0.1:
            body_color = (255, 120, 120)

        pygame.draw.circle(char_surf, body_color, (draw_cx, draw_cy), radius)

        # Highlight/Glow
        pygame.draw.circle(
            char_surf,
            secondary_color,
            (draw_cx - radius // 3, draw_cy - radius // 3),
            max(2, radius // 4),
        )

        # 3. Draw Skin Specific features
        cls.draw_skin_features(char_surf, draw_cx, draw_cy, radius, skin_name, primary_color, secondary_color)

        # 4. Look in direction of movement if moving
        look_x, look_y = 0, 0
        if is_moving and player is not None:
            last_dir = getattr(player, "last_move_direction", (0, 0))
            if len(last_dir) >= 2:
                dr, dc = last_dir[0], last_dir[1]
                if dc > 0: look_x = 2
                elif dc < 0: look_x = -2
                if dr > 0: look_y = 2
                elif dr < 0: look_y = -2
            if look_x == 0 and look_y == 0:
                tx = getattr(player, "target_x", cx)
                ty = getattr(player, "target_y", cy)
                px_pos = getattr(player, "x", cx)
                py_pos = getattr(player, "y", cy)
                if tx - px_pos > 1: look_x = 2
                elif tx - px_pos < -1: look_x = -2
                if ty - py_pos > 1: look_y = 2
                elif ty - py_pos < -1: look_y = -2

        # 5. Draw Eyes (with blinking support)
        is_blinking = (ticks % 4500) > 4350
        eye_color = (255, 255, 255)
        if "Ninja" in skin_name: eye_color = (245, 82, 95)
        elif "Mage" in skin_name or "Hacker" in skin_name: eye_color = (69, 230, 154)
        elif "Ice" in skin_name or "Frost" in skin_name: eye_color = (89, 145, 255)
        elif "Ghost" in skin_name or "Witch" in skin_name: eye_color = (255, 220, 100)
        elif "Pharaoh" in skin_name or "Guardian" in skin_name: eye_color = (0, 245, 255)

        eye_offset_x = max(3, radius // 3)
        eye_offset_y = max(2, radius // 5)
        eye_r = max(1, radius // 7)

        left_eye_pos = (draw_cx - eye_offset_x + look_x, draw_cy - eye_offset_y + look_y)
        right_eye_pos = (draw_cx + eye_offset_x + look_x, draw_cy - eye_offset_y + look_y)

        if is_blinking:
            pygame.draw.line(char_surf, eye_color, (left_eye_pos[0] - eye_r, left_eye_pos[1]), (left_eye_pos[0] + eye_r, left_eye_pos[1]), width=2)
            pygame.draw.line(char_surf, eye_color, (right_eye_pos[0] - eye_r, right_eye_pos[1]), (right_eye_pos[0] + eye_r, right_eye_pos[1]), width=2)
        else:
            pygame.draw.circle(char_surf, eye_color, left_eye_pos, eye_r)
            pygame.draw.circle(char_surf, eye_color, right_eye_pos, eye_r)

        # Blit Ghost surface with transparency if active
        if is_ghost:
            pygame.draw.circle(surface, (100, 240, 255, 90), (cx, render_cy), radius + 6, width=2)
            char_surf.set_alpha(150)
            surface.blit(char_surf, (cx - radius * 2, render_cy - radius * 2))

    @classmethod
    def draw_accessory(cls, surface, cx, cy, radius, name, is_moving=False):
        if name not in cls.ACCESSORIES:
            return
        meta = cls.ACCESSORIES[name]
        color = meta["color"]
        style = meta["style"]
        ticks = pygame.time.get_ticks()

        if style == "scarf":
            speed = 0.02 if is_moving else 0.01
            offset = math.sin(ticks * speed) * 4
            pygame.draw.polygon(
                surface,
                color,
                [
                    (cx - radius + 2, cy + radius // 3),
                    (cx - radius - 8, cy + radius + int(offset)),
                    (cx - radius - 3, cy + radius + 4 + int(offset)),
                    (cx, cy + radius // 2),
                ],
            )
        elif style == "wings":
            speed = 0.025 if is_moving else 0.015
            flap = math.sin(ticks * speed) * 6
            pygame.draw.ellipse(surface, color, (cx - radius - 10, cy - radius + 2, 10, int(radius + flap)))
            pygame.draw.ellipse(surface, color, (cx + radius, cy - radius + 2, 10, int(radius + flap)))
        elif style == "cloak":
            wave = math.sin(ticks * 0.01) * 3 if is_moving else 0
            pygame.draw.polygon(
                surface,
                color,
                [
                    (cx - radius, cy),
                    (cx - radius - 4 + int(wave), cy + radius + 4),
                    (cx + radius + 4 + int(wave), cy + radius + 4),
                    (cx + radius, cy),
                ],
            )
        elif style == "hat":
            pygame.draw.polygon(
                surface,
                color,
                [(cx - radius - 4, cy - radius + 3), (cx, cy - radius - 14), (cx + radius + 4, cy - radius + 3)]
            )
            pygame.draw.ellipse(surface, (color[0] // 2, color[1] // 2, color[2] // 2), (cx - radius - 6, cy - radius, radius * 2 + 12, 6))
        elif style == "visor":
            pygame.draw.rect(surface, color, (cx - radius + 2, cy - radius // 3, radius * 2 - 4, 6), border_radius=2)
        elif style == "crown":
            pygame.draw.polygon(
                surface,
                color,
                [(cx - radius + 3, cy - radius + 1), (cx - radius - 2, cy - radius - 8), (cx + radius + 2, cy - radius - 8), (cx + radius - 3, cy - radius + 1)]
            )

    @classmethod
    def draw_skin_features(cls, surface, cx, cy, radius, name, primary, secondary):
        if "Ninja" in name:
            pygame.draw.rect(surface, secondary, (cx - radius - 2, cy - 3, 4, 6))
            pygame.draw.circle(surface, secondary, (cx - radius - 4, cy - 1), 3)
        elif "Explorer" in name or "Scout" in name:
            pygame.draw.polygon(
                surface,
                (140, 110, 80),
                [(cx - radius, cy - radius // 3), (cx + radius, cy - radius // 3), (cx + radius + 4, cy - radius - 2), (cx - radius - 4, cy - radius - 2)]
            )
        elif "Mage" in name or "Fairy" in name:
            pygame.draw.circle(surface, secondary, (cx, cy + radius // 3), 2)
        elif "Warrior" in name or "Knight" in name:
            pygame.draw.rect(surface, (200, 200, 200), (cx - radius + 2, cy - 2, radius * 2 - 4, 4))
            pygame.draw.line(surface, (50, 50, 50), (cx - radius + 3, cy), (cx + radius - 3, cy), width=1)
        elif "Witch" in name:
            pygame.draw.polygon(
                surface,
                (40, 30, 60),
                [(cx - radius - 2, cy - radius + 2), (cx, cy - radius - 10), (cx + radius + 2, cy - radius + 2)]
            )
        elif "Skeleton" in name:
            pygame.draw.rect(surface, (20, 20, 20), (cx - 2, cy + 2, 4, radius // 2))
            pygame.draw.line(surface, (20, 20, 20), (cx - 4, cy + 5), (cx + 4, cy + 5), width=2)
        elif "Hacker" in name or "Android" in name:
            pygame.draw.rect(surface, (50, 255, 120), (cx - radius // 2, cy - 1, radius, 2))
        elif "Pharaoh" in name:
            pygame.draw.polygon(
                surface,
                (255, 215, 0),
                [(cx - radius + 3, cy - radius + 1), (cx - radius - 2, cy - radius - 8), (cx + radius + 2, cy - radius - 8), (cx + radius - 3, cy - radius + 1)]
            )

    @classmethod
    def get_unlock_info(cls, item_name):
        """
        Retrieves level/stars milestone criteria required to unlock cosmetics.
        """
        requirements = {
            "Crimson Ninja": "Complete Level 1-2",
            "Blue Moon Ninja": "Complete Level 1-3",
            "White Ronin": "Complete Level 1-4",
            "Masked Kunoichi": "Defeat World 1 Boss",

            "Flower Mage": "Complete Level 2-2",
            "Butterfly Knight": "Complete Level 2-3",
            "Garden Fairy": "Complete Level 2-4",
            "Nature Guardian": "Defeat World 2 Boss",

            "Snow Scout": "Complete Level 3-2",
            "Frost Mage": "Complete Level 3-3",
            "Arctic Explorer": "Complete Level 3-4",
            "Crystal Knight": "Defeat World 3 Boss",

            "Little Witch": "Complete Level 4-2",
            "Skeleton Hero": "Complete Level 4-3",
            "Cursed Knight": "Complete Level 4-4",
            "Victorian Explorer": "Defeat World 4 Boss",

            "Neon Hacker": "Complete Level 5-2",
            "Battle Android": "Complete Level 5-3",
            "Glitch Runner": "Complete Level 5-4",
            "Robot Scout": "Defeat World 5 Boss",

            "Desert Guardian": "Complete Level 6-2",
            "Pharaoh Warrior": "Complete Level 6-3",
            "Sand Mage": "Complete Level 6-4",
            "Temple Explorer": "Defeat World 6 Boss",
        }
        return requirements.get(item_name, "Unlocked by default")
