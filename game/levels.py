class LevelConfig:
    """
    Configuration template for a single maze level.
    """
    def __init__(
        self,
        level_id,
        world_id,
        level_number,
        display_name,
        rows=15,
        cols=15,
        battery_drain=1.0,
        battery_count=4,
        powerup_count=2,
        trap_count=3,
        door_count=0,
        monster_count=0,
        monster_speed=1.5,
        monster_damage=10,
        visibility_radius=4,
        time_target=45,
        move_target=60,
        score_multiplier=1.0,
        special_rules=None,
        is_boss_level=False
    ):
        self.level_id = level_id
        self.world_id = world_id
        self.level_number = level_number
        self.display_name = display_name
        self.rows = rows
        self.cols = cols
        self.battery_drain = battery_drain
        self.battery_count = battery_count
        self.powerup_count = powerup_count
        self.trap_count = trap_count
        self.door_count = door_count
        self.monster_count = monster_count
        self.monster_speed = monster_speed
        self.monster_damage = monster_damage
        self.visibility_radius = visibility_radius
        self.time_target = time_target
        self.move_target = move_target
        self.score_multiplier = score_multiplier
        self.special_rules = special_rules if special_rules else []
        self.is_boss_level = is_boss_level


class WorldConfig:
    """
    Configuration template for a themed world containing levels.
    """
    def __init__(self, world_id, name, theme_name, description):
        self.world_id = world_id
        self.name = name
        self.theme_name = theme_name
        self.description = description
        self.levels = []


class LevelManager:
    """
    Registry for loading and querying world and level configurations.
    """

    WORLDS = {
        "1": WorldConfig("1", "Ninja Village", "Ninja World", "Sneak through lantern-lit black wooden village paths under a crimson moon."),
        "2": WorldConfig("2", "Spring Canopy", "Spring World", "Explore flower hedges and vine tunnels of a bright magical green garden."),
        "3": WorldConfig("3", "Frostbound Glades", "Frozen World", "Navigate slippery cracked ice floes and frost spikes inside deep auroral caves."),
        "4": WorldConfig("4", "Whispering crypts", "Haunted World", "Dodge graveyard ghosts and screeching floor traps inside a foggy haunted estate."),
        "5": WorldConfig("5", "Neon Grid", "Cyber World", "Infiltrate circuits, holo portals, and reversing glitches in a neon hacker metropolis."),
        "6": WorldConfig("6", "Sandstone Tomb", "Desert Temple World", "Uncover ancient scarab shrines and stone blockades beneath sandstorm ruins."),
    }

    LEVELS = {}

    @classmethod
    def initialize(cls):
        """
        Creates all 30 level configurations dynamically with detailed balance curves.
        """
        cls.LEVELS.clear()
        for w_id in cls.WORLDS:
            cls.WORLDS[w_id].levels.clear()

        # Helper to construct levels
        # World 1: Ninja Village (Easy entry point)
        cls._add_level(LevelConfig("1-1", "1", 1, "The Quiet Night", rows=13, cols=13, battery_drain=0.5, battery_count=5, powerup_count=2, trap_count=1, door_count=0, monster_count=0, visibility_radius=4, time_target=35, move_target=50, score_multiplier=1.0))
        cls._add_level(LevelConfig("1-2", "1", 2, "Bamboo Shadows", rows=15, cols=15, battery_drain=0.8, battery_count=5, powerup_count=3, trap_count=3, door_count=0, monster_count=1, monster_speed=1.4, monster_damage=10, visibility_radius=4, time_target=50, move_target=70, score_multiplier=1.1))
        cls._add_level(LevelConfig("1-3", "1", 3, "Lantern Trails", rows=17, cols=17, battery_drain=1.0, battery_count=4, powerup_count=3, trap_count=5, door_count=1, monster_count=1, monster_speed=1.2, monster_damage=15, visibility_radius=3, time_target=75, move_target=100, score_multiplier=1.3))
        cls._add_level(LevelConfig("1-4", "1", 4, "Ink and Steel", rows=19, cols=19, battery_drain=1.2, battery_count=4, powerup_count=2, trap_count=7, door_count=2, monster_count=1, monster_speed=1.0, monster_damage=20, visibility_radius=3, time_target=95, move_target=130, score_multiplier=1.5))
        cls._add_level(LevelConfig("1-5", "1", 5, "Shogun Escape", rows=21, cols=21, battery_drain=1.4, battery_count=3, powerup_count=2, trap_count=10, door_count=3, monster_count=1, monster_speed=0.75, monster_damage=25, visibility_radius=3, time_target=120, move_target=160, score_multiplier=2.0, is_boss_level=True, special_rules=["Ninja Clones"]))

        # World 2: Spring Canopy
        cls._add_level(LevelConfig("2-1", "2", 1, "Blooming Paths", rows=15, cols=15, battery_drain=0.7, battery_count=6, powerup_count=4, trap_count=2, door_count=0, monster_count=0, visibility_radius=4, time_target=45, move_target=60, score_multiplier=1.2))
        cls._add_level(LevelConfig("2-2", "2", 2, "Hedge Labyrinth", rows=17, cols=17, battery_drain=1.0, battery_count=5, powerup_count=3, trap_count=4, door_count=1, monster_count=1, monster_speed=1.3, monster_damage=12, visibility_radius=4, time_target=65, move_target=90, score_multiplier=1.3))
        cls._add_level(LevelConfig("2-3", "2", 3, "Whispering Roots", rows=19, cols=19, battery_drain=1.2, battery_count=4, powerup_count=3, trap_count=6, door_count=1, monster_count=1, monster_speed=1.1, monster_damage=15, visibility_radius=3, time_target=85, move_target=120, score_multiplier=1.5))
        cls._add_level(LevelConfig("2-4", "2", 4, "Overgrown Thickets", rows=21, cols=21, battery_drain=1.4, battery_count=4, powerup_count=2, trap_count=9, door_count=2, monster_count=1, monster_speed=0.9, monster_damage=20, visibility_radius=3, time_target=110, move_target=150, score_multiplier=1.8))
        cls._add_level(LevelConfig("2-5", "2", 5, "Floral Monarch", rows=23, cols=23, battery_drain=1.6, battery_count=3, powerup_count=2, trap_count=12, door_count=3, monster_count=1, monster_speed=0.70, monster_damage=25, visibility_radius=3, time_target=140, move_target=200, score_multiplier=2.4, is_boss_level=True, special_rules=["Ivy Overgrowth"]))

        # World 3: Frostbound Glades
        cls._add_level(LevelConfig("3-1", "3", 1, "Slippery Slope", rows=15, cols=15, battery_drain=0.9, battery_count=5, powerup_count=3, trap_count=3, door_count=0, monster_count=0, visibility_radius=4, time_target=50, move_target=70, score_multiplier=1.4))
        cls._add_level(LevelConfig("3-2", "3", 2, "Crystal Tunnels", rows=17, cols=17, battery_drain=1.1, battery_count=4, powerup_count=3, trap_count=5, door_count=1, monster_count=1, monster_speed=1.2, monster_damage=15, visibility_radius=3, time_target=75, move_target=100, score_multiplier=1.6))
        cls._add_level(LevelConfig("3-3", "3", 3, "Glacial Maze", rows=19, cols=19, battery_drain=1.3, battery_count=4, powerup_count=2, trap_count=7, door_count=2, monster_count=1, monster_speed=1.0, monster_damage=18, visibility_radius=3, time_target=95, move_target=135, score_multiplier=1.8))
        cls._add_level(LevelConfig("3-4", "3", 4, "Aurora Depths", rows=21, cols=21, battery_drain=1.5, battery_count=3, powerup_count=2, trap_count=9, door_count=2, monster_count=1, monster_speed=0.8, monster_damage=22, visibility_radius=2, time_target=115, move_target=160, score_multiplier=2.1))
        cls._add_level(LevelConfig("3-5", "3", 5, "Ice Skull Chase", rows=23, cols=23, battery_drain=1.8, battery_count=3, powerup_count=2, trap_count=13, door_count=3, monster_count=1, monster_speed=0.60, monster_damage=30, visibility_radius=3, time_target=150, move_target=210, score_multiplier=2.8, is_boss_level=True, special_rules=["Slippery Slide"]))

        # World 4: Whispering Crypts
        cls._add_level(LevelConfig("4-1", "4", 1, "Forgotten Graves", rows=15, cols=15, battery_drain=1.0, battery_count=5, powerup_count=3, trap_count=3, door_count=0, monster_count=1, monster_speed=1.5, monster_damage=12, visibility_radius=3, time_target=55, move_target=75, score_multiplier=1.5))
        cls._add_level(LevelConfig("4-2", "4", 2, "Tombstone Alley", rows=17, cols=17, battery_drain=1.2, battery_count=4, powerup_count=3, trap_count=6, door_count=1, monster_count=1, monster_speed=1.2, monster_damage=15, visibility_radius=3, time_target=75, move_target=105, score_multiplier=1.7))
        cls._add_level(LevelConfig("4-3", "4", 3, "Spectre Mansion", rows=19, cols=19, battery_drain=1.4, battery_count=4, powerup_count=2, trap_count=8, door_count=2, monster_count=1, monster_speed=0.95, monster_damage=20, visibility_radius=3, time_target=100, move_target=140, score_multiplier=1.9))
        cls._add_level(LevelConfig("4-4", "4", 4, "Phantom Crypts", rows=21, cols=21, battery_drain=1.6, battery_count=3, powerup_count=2, trap_count=10, door_count=2, monster_count=1, monster_speed=0.75, monster_damage=25, visibility_radius=2, time_target=125, move_target=180, score_multiplier=2.3))
        cls._add_level(LevelConfig("4-5", "4", 5, "Reaper Escape", rows=23, cols=23, battery_drain=1.9, battery_count=3, powerup_count=1, trap_count=14, door_count=3, monster_count=1, monster_speed=0.55, monster_damage=35, visibility_radius=3, time_target=160, move_target=230, score_multiplier=3.2, is_boss_level=True, special_rules=["Ghost Walls"]))

        # World 5: Neon Grid
        cls._add_level(LevelConfig("5-1", "5", 1, "Digital Grid", rows=15, cols=15, battery_drain=1.1, battery_count=5, powerup_count=3, trap_count=4, door_count=1, monster_count=1, monster_speed=1.3, monster_damage=15, visibility_radius=3, time_target=60, move_target=80, score_multiplier=1.8))
        cls._add_level(LevelConfig("5-2", "5", 2, "Hologram Maze", rows=17, cols=17, battery_drain=1.3, battery_count=4, powerup_count=3, trap_count=7, door_count=1, monster_count=1, monster_speed=1.1, monster_damage=18, visibility_radius=3, time_target=80, move_target=115, score_multiplier=2.0))
        cls._add_level(LevelConfig("5-3", "5", 3, "Circuit Breaker", rows=19, cols=19, battery_drain=1.5, battery_count=4, powerup_count=2, trap_count=9, door_count=2, monster_count=1, monster_speed=0.9, monster_damage=22, visibility_radius=3, time_target=105, move_target=150, score_multiplier=2.3))
        cls._add_level(LevelConfig("5-4", "5", 4, "Data Streams", rows=21, cols=21, battery_drain=1.7, battery_count=3, powerup_count=2, trap_count=11, door_count=2, monster_count=1, monster_speed=0.7, monster_damage=28, visibility_radius=2, time_target=130, move_target=190, score_multiplier=2.7))
        cls._add_level(LevelConfig("5-5", "5", 5, "Overlord Mainframe", rows=23, cols=23, battery_drain=2.0, battery_count=3, powerup_count=2, trap_count=15, door_count=3, monster_count=1, monster_speed=0.50, monster_damage=40, visibility_radius=3, time_target=170, move_target=245, score_multiplier=3.8, is_boss_level=True, special_rules=["Glitch Swaps"]))

        # World 6: Sandstone Tomb
        cls._add_level(LevelConfig("6-1", "6", 1, "Dust and Stone", rows=17, cols=17, battery_drain=1.2, battery_count=5, powerup_count=3, trap_count=5, door_count=1, monster_count=1, monster_speed=1.1, monster_damage=18, visibility_radius=3, time_target=75, move_target=100, score_multiplier=2.2))
        cls._add_level(LevelConfig("6-2", "6", 2, "Anubis Sanctum", rows=19, cols=19, battery_drain=1.4, battery_count=4, powerup_count=3, trap_count=8, door_count=2, monster_count=1, monster_speed=0.9, monster_damage=22, visibility_radius=3, time_target=95, move_target=135, score_multiplier=2.5))
        cls._add_level(LevelConfig("6-3", "6", 3, "Scarab Labyrinth", rows=21, cols=21, battery_drain=1.6, battery_count=3, powerup_count=2, trap_count=10, door_count=2, monster_count=1, monster_speed=0.75, monster_damage=28, visibility_radius=3, time_target=125, move_target=175, score_multiplier=2.9))
        cls._add_level(LevelConfig("6-4", "6", 4, "Chamber of Trials", rows=23, cols=23, battery_drain=1.9, battery_count=3, powerup_count=2, trap_count=13, door_count=3, monster_count=1, monster_speed=0.6, monster_damage=35, visibility_radius=2, time_target=150, move_target=215, score_multiplier=3.4))
        cls._add_level(LevelConfig("6-5", "6", 5, "Tomb of Pharaohs", rows=25, cols=25, battery_drain=2.2, battery_count=2, powerup_count=1, trap_count=16, door_count=3, monster_count=1, monster_speed=0.45, monster_damage=45, visibility_radius=3, time_target=190, move_target=280, score_multiplier=4.5, is_boss_level=True, special_rules=["Sandstorms"]))

    @classmethod
    def _add_level(cls, config):
        cls.LEVELS[config.level_id] = config
        cls.WORLDS[config.world_id].levels.append(config)

    @classmethod
    def get_level(cls, level_id):
        if not cls.LEVELS:
            cls.initialize()
        return cls.LEVELS.get(level_id)

    @classmethod
    def get_world(cls, world_id):
        if not cls.LEVELS:
            cls.initialize()
        return cls.WORLDS.get(world_id)

    @classmethod
    def get_next_level_id(cls, current_level_id):
        parts = current_level_id.split("-")
        w = parts[0]
        lv = int(parts[1])
        
        # Try next level in same world
        next_in_world = f"{w}-{lv + 1}"
        if next_in_world in cls.LEVELS:
            return next_in_world

        # Try first level of next world
        next_w_id = str(int(w) + 1)
        next_world_first = f"{next_w_id}-1"
        if next_world_first in cls.LEVELS:
            return next_world_first

        return None
