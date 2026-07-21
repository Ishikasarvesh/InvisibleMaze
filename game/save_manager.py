import os
import json

class SaveManager:
    """
    Manages loading, saving, and recovering game progress, scores, stars,
    and character cosmetics settings to/from save_data.json.
    """

    FILE_PATH = "save_data.json"

    @classmethod
    def get_default_data(cls):
        """
        Returns a fresh progress layout unlocking only World 1 Level 1.
        """
        return {
            "completed_levels": [],
            "unlocked_levels": ["1-1"],
            "highest_score": {},
            "best_time": {},
            "best_moves": {},
            "stars_earned": {},
            "selected_theme": "Ninja World",
            "selected_skin_by_world": {
                "1": "Shadow Ninja",
                "2": "Forest Explorer",
                "3": "Ice Warrior",
                "4": "Ghost Hunter",
                "5": "Cyber Ninja",
                "6": "Treasure Hunter",
            },
            "selected_colors_by_world": {
                "1": [(0, 0, 0), (245, 82, 95)],
                "2": [(75, 140, 90), (255, 255, 255)],
                "3": [(110, 180, 255), (255, 255, 255)],
                "4": [(100, 75, 125), (255, 220, 100)],
                "5": [(15, 230, 180), (0, 0, 0)],
                "6": [(220, 160, 60), (255, 255, 255)],
            },
            "selected_accessories_by_world": {
                "1": "Scarlet Scarf",
                "2": "Fairy Wings",
                "3": "Fur Cloak",
                "4": "Witch Hat",
                "5": "Neon Visor",
                "6": "Pharaoh Mask",
            },
            "unlocked_skins": ["Shadow Ninja", "Forest Explorer", "Ice Warrior", "Ghost Hunter", "Cyber Ninja", "Treasure Hunter"],
            "unlocked_cosmetics": ["Scarlet Scarf", "Fairy Wings", "Fur Cloak", "Witch Hat", "Neon Visor", "Pharaoh Mask"],
        }

    @classmethod
    def load(cls):
        """
        Loads the save file safely. Recovers with defaults if corrupted.
        """
        if not os.path.exists(cls.FILE_PATH):
            data = cls.get_default_data()
            cls.save(data)
            return data

        try:
            with open(cls.FILE_PATH, "r") as f:
                data = json.load(f)
                
                # Validation: ensure essential keys are present
                default_data = cls.get_default_data()
                for key, val in default_data.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            # Corrupted backup recovery
            try:
                if os.path.exists(cls.FILE_PATH):
                    backup_path = cls.FILE_PATH + ".bak"
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(cls.FILE_PATH, backup_path)
            except Exception:
                pass
            
            data = cls.get_default_data()
            cls.save(data)
            return data

    @classmethod
    def save(cls, data):
        """
        Writes data safely to save_data.json.
        """
        try:
            temp_path = cls.FILE_PATH + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=4)
            if os.path.exists(cls.FILE_PATH):
                os.remove(cls.FILE_PATH)
            os.rename(temp_path, cls.FILE_PATH)
            return True
        except Exception:
            return False
