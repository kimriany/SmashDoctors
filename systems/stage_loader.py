import json
import pygame


class StageLoader:
    def __init__(self, path):
        self.path = path

    def load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        platforms = []
        for p in raw_data["platforms"]:
            platforms.append(
                pygame.Rect(
                    p["x"],
                    p["y"],
                    p["w"],
                    p["h"],
                )
            )

        return {
            "name": raw_data["name"],
            "platforms": platforms,
            "player_spawn": raw_data.get("player_spawn", [100, 100]),
            "boss_spawn": raw_data.get("boss_spawn", [700, 100]),
        }
