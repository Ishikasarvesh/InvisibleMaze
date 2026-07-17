import pygame


# =========================================================
# WINDOW SETTINGS
# =========================================================

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 760
FPS = 60

GAME_TITLE = "Invisible Maze"


# =========================================================
# GAME STATES
# =========================================================

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_WON = "won"
STATE_SETTINGS = "settings"


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

WALL_COLOR = (63, 72, 100)
WALL_EDGE = (94, 108, 145)

PATH_COLOR = (22, 28, 43)
PATH_EDGE = (35, 43, 64)

HIDDEN_COLOR = (2, 3, 7)
VISITED_COLOR = (29, 34, 49)

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
        "battery_pickups": 5,
        "battery_restore": 25,
        "score_bonus": 1800,
        "time_multiplier": 1.4,
    },

    "Hard": {
        "rows": 25,
        "cols": 25,
        "starting_battery": 80,
        "battery_drain": 2.4,
        "maximum_visibility": 3,
        "minimum_visibility": 1,
        "battery_pickups": 4,
        "battery_restore": 20,
        "score_bonus": 2800,
        "time_multiplier": 1.8,
    },
}


# =========================================================
# LAYOUT
# =========================================================

HUD_HEIGHT = 86
BOTTOM_BAR_HEIGHT = 48

MAZE_TOP_MARGIN = 105
MAZE_SIDE_MARGIN = 65
MAZE_BOTTOM_MARGIN = 70


# =========================================================
# ANIMATION SETTINGS
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
            bold=True
        ),

        "heading": pygame.font.SysFont(
            "segoeui",
            38,
            bold=True
        ),

        "subheading": pygame.font.SysFont(
            "segoeui",
            26,
            bold=True
        ),

        "body": pygame.font.SysFont(
            "segoeui",
            20
        ),

        "small": pygame.font.SysFont(
            "segoeui",
            16
        ),

        "tiny": pygame.font.SysFont(
            "segoeui",
            13
        ),
    }