import game.settings
import game.maze
import ui.hud
import ui.menu
import ui.pause_screen
import ui.result_screen
import ui.transitions

class Theme:
    """
    Holds colors, palettes, and style configurations for a specific theme world.
    """
    def __init__(
        self,
        name,
        background,
        background_secondary,
        wall_color,
        wall_edge,
        path_color,
        path_edge,
        visited_color,
        panel,
        panel_border,
        yellow,
        blue,
        green,
        orange,
        red,
        white,
        text_secondary,
        text_muted,
        particle_palette,
        exit_style="portal",
        ambient_effect="none"
    ):
        self.name = name
        self.background = background
        self.background_secondary = background_secondary
        self.wall_color = wall_color
        self.wall_edge = wall_edge
        self.path_color = path_color
        self.path_edge = path_edge
        self.visited_color = visited_color
        self.panel = panel
        self.panel_border = panel_border
        self.yellow = yellow
        self.blue = blue
        self.green = green
        self.orange = orange
        self.red = red
        self.white = white
        self.text_secondary = text_secondary
        self.text_muted = text_muted
        self.particle_palette = particle_palette
        self.exit_style = exit_style
        self.ambient_effect = ambient_effect


class ThemeManager:
    """
    Manages loading, updating, and applying theme visuals dynamically.
    """

    THEMES = {
        "Ninja World": Theme(
            name="Ninja World",
            background=(10, 10, 15),
            background_secondary=(18, 14, 22),
            wall_color=(25, 20, 25),      # Black wooden walls
            wall_edge=(245, 82, 95),       # Red ropes
            path_color=(15, 12, 18),      # Lantern-lit path
            path_edge=(220, 180, 70),     # Soft gold paths
            visited_color=(35, 25, 30),
            panel=(18, 14, 22),
            panel_border=(245, 82, 95),
            yellow=(220, 180, 70),
            blue=(89, 145, 255),
            green=(69, 230, 154),
            orange=(230, 130, 60),
            red=(245, 82, 95),
            white=(240, 240, 245),
            text_secondary=(150, 145, 160),
            text_muted=(90, 85, 100),
            particle_palette=[(245, 82, 95), (255, 182, 193), (255, 255, 255)], # Red / Pink blossoms
            exit_style="torii_gate",
            ambient_effect="blossoms"
        ),

        "Spring World": Theme(
            name="Spring World",
            background=(15, 32, 20),
            background_secondary=(22, 45, 28),
            wall_color=(35, 75, 45),       # Hedge walls
            wall_edge=(155, 230, 140),     # Flower highlights
            path_color=(20, 38, 25),       # Mossy stones
            path_edge=(80, 160, 105),
            visited_color=(40, 65, 48),
            panel=(22, 45, 28),
            panel_border=(155, 230, 140),
            yellow=(255, 215, 70),
            blue=(100, 200, 255),
            green=(69, 230, 154),
            orange=(240, 160, 80),
            red=(250, 100, 110),
            white=(245, 250, 245),
            text_secondary=(170, 200, 180),
            text_muted=(110, 140, 120),
            particle_palette=[(155, 230, 140), (255, 255, 180), (255, 182, 193)], # Leaves / Petals
            exit_style="flower_portal",
            ambient_effect="butterflies"
        ),

        "Frozen World": Theme(
            name="Frozen World",
            background=(10, 20, 32),
            background_secondary=(15, 28, 48),
            wall_color=(30, 58, 85),       # Translucent ice walls
            wall_edge=(140, 210, 255),     # aurora border
            path_color=(15, 26, 40),       # snow paths
            path_edge=(80, 130, 180),
            visited_color=(35, 52, 70),
            panel=(15, 28, 48),
            panel_border=(140, 210, 255),
            yellow=(255, 220, 100),
            blue=(89, 145, 255),
            green=(120, 250, 200),
            orange=(230, 150, 80),
            red=(245, 95, 110),
            white=(250, 250, 255),
            text_secondary=(170, 195, 220),
            text_muted=(110, 135, 160),
            particle_palette=[(140, 210, 255), (255, 255, 255), (100, 180, 255)], # Snow flakes
            exit_style="aurora",
            ambient_effect="aurora"
        ),

        "Haunted World": Theme(
            name="Haunted World",
            background=(12, 8, 16),
            background_secondary=(20, 15, 26),
            wall_color=(28, 22, 32),       # Grave markers
            wall_edge=(160, 120, 210),     # Web accents
            path_color=(16, 12, 20),
            path_edge=(90, 75, 110),
            visited_color=(32, 24, 38),
            panel=(20, 15, 26),
            panel_border=(160, 120, 210),
            yellow=(255, 215, 0),
            blue=(140, 170, 255),
            green=(110, 245, 170),
            orange=(240, 125, 50),
            red=(245, 95, 95),
            white=(230, 225, 235),
            text_secondary=(160, 150, 175),
            text_muted=(95, 88, 105),
            particle_palette=[(160, 120, 210), (100, 200, 220), (50, 50, 50)], # Ghost flames
            exit_style="spirit_portal",
            ambient_effect="fog"
        ),

        "Cyber World": Theme(
            name="Cyber World",
            background=(5, 5, 10),
            background_secondary=(12, 10, 22),
            wall_color=(15, 18, 30),       # Grid board walls
            wall_edge=(0, 245, 255),       # Cyan lasers
            path_color=(8, 10, 18),
            path_edge=(0, 160, 180),
            visited_color=(20, 30, 42),
            panel=(12, 10, 22),
            panel_border=(0, 245, 255),
            yellow=(255, 255, 0),
            blue=(0, 150, 255),
            green=(50, 255, 120),
            orange=(255, 128, 0),
            red=(255, 45, 85),
            white=(240, 255, 250),
            text_secondary=(140, 180, 190),
            text_muted=(80, 110, 120),
            particle_palette=[(0, 245, 255), (50, 255, 120), (255, 45, 85)], # Glitch code streams
            exit_style="glitch_portal",
            ambient_effect="grid_glow"
        ),

        "Desert Temple World": Theme(
            name="Desert Temple World",
            background=(32, 22, 12),
            background_secondary=(48, 35, 18),
            wall_color=(85, 65, 40),       # Sandstone carvings
            wall_edge=(255, 210, 100),     # Torches glow
            path_color=(36, 25, 15),
            path_edge=(160, 120, 70),
            visited_color=(60, 48, 32),
            panel=(48, 35, 18),
            panel_border=(255, 210, 100),
            yellow=(255, 210, 100),
            blue=(100, 180, 255),
            green=(140, 245, 150),
            orange=(240, 140, 50),
            red=(245, 90, 90),
            white=(250, 245, 235),
            text_secondary=(200, 180, 155),
            text_muted=(135, 115, 90),
            particle_palette=[(255, 210, 100), (220, 160, 60), (250, 240, 210)], # Sand/Dust
            exit_style="sand_portal",
            ambient_effect="sandstorm"
        )
    }

    @classmethod
    def apply_theme(cls, theme_name):
        """
        Dynamically overrides global Pygame variables across module dictionaries
        for immediate visual synchronizations.
        """
        theme = cls.THEMES.get(theme_name)
        if not theme:
            return

        # Override game.settings
        game.settings.BACKGROUND = theme.background
        game.settings.BACKGROUND_SECONDARY = theme.background_secondary
        game.settings.WALL_COLOR = theme.wall_color
        game.settings.WALL_EDGE = theme.wall_edge
        game.settings.PATH_COLOR = theme.path_color
        game.settings.PATH_EDGE = theme.path_edge
        game.settings.HIDDEN_COLOR = (
            int(theme.background[0] * 0.4),
            int(theme.background[1] * 0.4),
            int(theme.background[2] * 0.4),
        )
        game.settings.VISITED_COLOR = theme.visited_color
        game.settings.PANEL = theme.panel
        game.settings.PANEL_BORDER = theme.panel_border
        game.settings.YELLOW = theme.yellow
        game.settings.BLUE = theme.blue
        game.settings.GREEN = theme.green
        game.settings.ORANGE = theme.orange
        game.settings.RED = theme.red
        game.settings.WHITE = theme.white
        game.settings.TEXT_SECONDARY = theme.text_secondary
        game.settings.TEXT_MUTED = theme.text_muted

        # Propagate to loaded modules
        modules = [game.game, game.maze, ui.hud, ui.menu, ui.pause_screen, ui.result_screen, ui.transitions]
        for mod in modules:
            if mod is None:
                continue
            if hasattr(mod, "BACKGROUND"): mod.BACKGROUND = theme.background
            if hasattr(mod, "BACKGROUND_SECONDARY"): mod.BACKGROUND_SECONDARY = theme.background_secondary
            if hasattr(mod, "WALL_COLOR"): mod.WALL_COLOR = theme.wall_color
            if hasattr(mod, "WALL_EDGE"): mod.WALL_EDGE = theme.wall_edge
            if hasattr(mod, "PATH_COLOR"): mod.PATH_COLOR = theme.path_color
            if hasattr(mod, "PATH_EDGE"): mod.PATH_EDGE = theme.path_edge
            if hasattr(mod, "HIDDEN_COLOR"): mod.HIDDEN_COLOR = (
                int(theme.background[0] * 0.4),
                int(theme.background[1] * 0.4),
                int(theme.background[2] * 0.4),
            )
            if hasattr(mod, "VISITED_COLOR"): mod.VISITED_COLOR = theme.visited_color
            if hasattr(mod, "PANEL"): mod.PANEL = theme.panel
            if hasattr(mod, "PANEL_BORDER"): mod.PANEL_BORDER = theme.panel_border
            if hasattr(mod, "YELLOW"): mod.YELLOW = theme.yellow
            if hasattr(mod, "BLUE"): mod.BLUE = theme.blue
            if hasattr(mod, "GREEN"): mod.GREEN = theme.green
            if hasattr(mod, "ORANGE"): mod.ORANGE = theme.orange
            if hasattr(mod, "RED"): mod.RED = theme.red
            if hasattr(mod, "WHITE"): mod.WHITE = theme.white
            if hasattr(mod, "TEXT_SECONDARY"): mod.TEXT_SECONDARY = theme.text_secondary
            if hasattr(mod, "TEXT_MUTED"): mod.TEXT_MUTED = theme.text_muted
