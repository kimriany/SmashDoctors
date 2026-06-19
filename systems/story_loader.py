"""
StoryLoader — story_config.json 로드 + 보스 클래스 동적 임포트

사용법:
    loader = StoryLoader()
    chapters = loader.chapters          # 챕터 목록
    boss_cls = loader.get_boss_class(chapter)
"""
import json
import importlib
import os


CONFIG_PATH = "data/story/story_config.json"

BOSS_CLASS_ALIASES = {
    "ro2t": "entities.Boss_characters.ro2t_boss.Ro2tBoss",
    "ro2tboss": "entities.Boss_characters.ro2t_boss.Ro2tBoss",
    "root2": "entities.Boss_characters.ro2t_boss.Ro2tBoss",
    "root2boss": "entities.Boss_characters.ro2t_boss.Ro2tBoss",
    "hora": "entities.Boss_characters.hora_boss.HoraBoss",
    "horaboss": "entities.Boss_characters.hora_boss.HoraBoss",
}


class StoryLoader:
    def __init__(self):
        self.title    = "SmashDoctors Story"
        self.chapters: list[dict] = []
        self._load()

    def _load(self):
        if not os.path.exists(CONFIG_PATH):
            print(f"[StoryLoader] 설정 파일 없음: {CONFIG_PATH}")
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.title    = data.get("title", self.title)
            self.chapters = data.get("chapters", [])
        except Exception as e:
            print(f"[StoryLoader] 로드 실패: {e}")

    def get_boss_class(self, chapter: dict):
        """
        chapter["boss_class"] 문자열로 클래스를 동적 임포트.
        실패 시 None 반환 → game.py에서 기본 Boss 사용.

        boss_class 형식: "entities.Boss_characters.MyBoss"
        """
        class_path = chapter.get("boss_class", "")
        if not class_path:
            return None

        class_path = self._normalize_boss_class_path(str(class_path))

        class_name = class_path.rsplit(".", 1)[-1]

        try:
            parts     = class_path.rsplit(".", 1)
            module    = importlib.import_module(parts[0])
            return getattr(module, parts[1])
        except Exception:
            pass

        try:
            module = importlib.import_module(f"entities.characters.{class_name}")
            return getattr(module, class_name)
        except Exception as e:
            print(f"[StoryLoader] 보스 클래스 로드 실패 ({class_path}): {e}")
            return None

    def _normalize_boss_class_path(self, class_path: str) -> str:
        compact = (
            class_path.strip()
            .lower()
            .replace("_", "")
            .replace("-", "")
            .replace(".", "")
        )
        for alias, real_path in BOSS_CLASS_ALIASES.items():
            if alias in compact:
                return real_path
        return class_path

    def get_chapter(self, chapter_id: int) -> dict | None:
        for c in self.chapters:
            if c["id"] == chapter_id:
                return c
        return None

    @property
    def total(self) -> int:
        return len(self.chapters)
