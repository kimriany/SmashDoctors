"""
StorySave — 스토리 진행 상태 저장/불러오기

저장 파일: data/story/save.json
형식:
{
    "cleared": [1, 2],          # 클리어한 챕터 ID 목록
    "selected_character": null, # 선택한 캐릭터 클래스명
    "play_count": { "1": 3 }    # 챕터별 플레이 횟수
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용법:
    save = StorySave()
    save.mark_cleared(1)        # 챕터 1 클리어
    save.is_cleared(1)          # True
    save.is_unlocked(2)         # True (챕터 1 클리어 후)
    save.reset()                # 초기화
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import os

SAVE_PATH = "data/story/save.json"


class StorySave:
    def __init__(self):
        self._data = {
            "cleared":    [],
            "selected_character": None,
            "play_count": {},
        }
        self._load()

    # ── 내부 IO ─────────────────────────────────────────────────
    def _load(self):
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
            except Exception as e:
                print(f"[StorySave] 불러오기 실패: {e}")

    def save(self):
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[StorySave] 저장 실패: {e}")

    # ── 챕터 상태 ───────────────────────────────────────────────
    def is_cleared(self, chapter_id: int) -> bool:
        return chapter_id in self._data["cleared"]

    def mark_cleared(self, chapter_id: int):
        if chapter_id not in self._data["cleared"]:
            self._data["cleared"].append(chapter_id)
        pc = self._data["play_count"]
        pc[str(chapter_id)] = pc.get(str(chapter_id), 0) + 1
        self.save()

    def is_unlocked(self, chapter: dict) -> bool:
        cond = chapter.get("unlock_condition")
        if cond is None:
            return True
        req = cond.get("clear_chapter")
        if req is not None:
            return self.is_cleared(req)
        return True

    def cleared_count(self) -> int:
        return len(self._data["cleared"])

    def play_count(self, chapter_id: int) -> int:
        return self._data["play_count"].get(str(chapter_id), 0)

    # ── 캐릭터 선택 기억 ────────────────────────────────────────
    def set_character(self, class_name: str):
        self._data["selected_character"] = class_name
        self.save()

    def get_character(self) -> str | None:
        return self._data.get("selected_character")

    # ── 초기화 ──────────────────────────────────────────────────
    def reset(self):
        self._data = {"cleared": [], "selected_character": None, "play_count": {}}
        self.save()
