import pygame


# =========================================================
# WINDOW SETTINGS
# =========================================================

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 760
FPS = 60

GAME_TITLE = "Invisible Maze"


# =========================================================
# DEBUG SETTINGS (OFF FOR NORMAL GAMEPLAY)
# =========================================================

DEBUG_DRAW_GRID = False
DEBUG_DRAW_PATHS = False
DEBUG_DRAW_COLLISION = False
DEBUG_DRAW_OBJECT_CELLS = False


# =========================================================
# GAME STATES
# =========================================================

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_WON = "won"
STATE_SETTINGS = "settings"

# Compatibility names used by game/game.py
GAME_STATE_MENU = STATE_MENU
GAME_STATE_PLAYING = STATE_PLAYING
GAME_STATE_PAUSED = STATE_PAUSED
GAME_STATE_WON = STATE_WON


# =========================================================
# COLORS
# =========================================================

BACKGROUND = (5, 7, 14)
BACKGROUND_SECONDARY = (10, 14, 25)

PANEL = (17, 22, 36)
PANEL_HOVER = (27, 34, 54)
PANEL_BORDER = (64, 78, 110)

WHITE = (245, 247, 255)
TEXT_SECONDARY = (165, 175, 200)
TEXT_MUTED = (95, 105, 130)

BLUE = (89, 145, 255)
BLUE_LIGHT = (145, 185, 255)

GREEN = (69, 230, 154)
GREEN_LIGHT = (145, 255, 205)

YELLOW = (255, 213, 92)
ORANGE = (255, 154, 70)
RED = (245, 82, 95)

WALL_COLOR = (45, 52, 75)
WALL_EDGE = (70, 80, 110)

PATH_COLOR = (12, 16, 26)
PATH_EDGE = (25, 32, 48)

HIDDEN_COLOR = (0, 0, 0)
VISITED_COLOR = (18, 22, 34)

PLAYER_COLOR = (255, 221, 116)
PLAYER_HIGHLIGHT = (255, 249, 207)

BATTERY_COLOR = (255, 207, 70)
BATTERY_GLOW = (255, 221, 105)

EXIT_COLOR = (71, 235, 171)
EXIT_CENTER = (174, 255, 219)


# =========================================================
# DIFFICULTY CONFIGURATION
# =========================================================

DIFFICULTIES = {
    "Easy": {
        "rows": 17,
        "cols": 17,
        "starting_battery": 100,
        "battery_drain": 1.0,
        "maximum_visibility": 4,
        "minimum_visibility": 2,
        "battery_pickups": 7,
        "battery_restore": 30,
        "score_bonus": 1000,
        "time_multiplier": 1.0,
    },

    "Medium": {
        "rows": 21,
        "cols": 21,
        "starting_battery": 90,
        "battery_drain": 1.7,
        "maximum_visibility": 3,
        "minimum_visibility": 1,
        "battery_pickups": 6,
        "battery_restore": 25,
        "score_bonus": 2000,
        "time_multiplier": 1.5,
    },

    "Hard": {
        "rows": 25,
        "cols": 25,
        "starting_battery": 80,
        "battery_drain": 2.5,
        "maximum_visibility": 2.5,
        "minimum_visibility": 1,
        "battery_pickups": 5,
        "battery_restore": 20,
        "score_bonus": 3500,
        "time_multiplier": 2.2,
    },

    "Extreme": {
        "rows": 29,
        "cols": 29,
        "starting_battery": 70,
        "battery_drain": 3.4,
        "maximum_visibility": 2,
        "minimum_visibility": 0.8,
        "battery_pickups": 4,
        "battery_restore": 15,
        "score_bonus": 5000,
        "time_multiplier": 3.0,
    },
}
DIFFICULTY_SETTINGS = DIFFICULTIES

DEFAULT_DIFFICULTY = "Easy"


# =========================================================
# HUD DIMENSIONS
# =========================================================

HUD_HEIGHT = 80
CARD_RADIUS = 12

MAZE_TOP_MARGIN = 20
MAZE_BOTTOM_MARGIN = 20
MAZE_SIDE_MARGIN = 20


# =========================================================
# ANIMATION SPEEDS & CONTROLS
# =========================================================

BUTTON_HOVER_SPEED = 8
BUTTON_PRESS_SCALE = 0.96

PLAYER_MOVE_SPEED = 12
PLAYER_PULSE_SPEED = 4.5

EXIT_PULSE_SPEED = 3.5
BATTERY_FLOAT_SPEED = 3

FADE_SPEED = 500

PARTICLE_COUNT = 35


# =========================================================
# FONT CREATION
# =========================================================

def create_fonts():
    return {
        "title": pygame.font.SysFont(
            "segoeui",
            64,
            bold=True,
        ),

        "heading": pygame.font.SysFont(
            "segoeui",
            38,
            bold=True,
        ),

        "subheading": pygame.font.SysFont(
            "segoeui",
            26,
            bold=True,
        ),

        "body": pygame.font.SysFont(
            "segoeui",
            20,
        ),

        "small": pygame.font.SysFont(
            "segoeui",
            16,
        ),

        "tiny": pygame.font.SysFont(
            "segoeui",
            13,
        ),
    }