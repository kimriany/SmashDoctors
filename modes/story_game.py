# modes/story_game.py

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from systems.font_manager import font

from scenes.character_select import CharacterSelect
from scenes.story_intro import StoryIntro
from scenes.story_stage_select import StoryStageSelect
from scenes.story_scene import StoryScene

from systems.story_save import StorySave
from systems.story_loader import StoryLoader

from engine.battle_session import BattleSession


class StoryState:
    INTRO = "intro"
    STAGE_SELECT = "stage_select"
    CHAR_SELECT = "char_select"
    SCENE = "scene"
    BATTLE = "battle"
    WIN = "win"
    LOSE = "lose"
    ENDING = "ending"


class StoryGame:
    def __init__(self, screen):
        self.screen = screen

        self.state = StoryState.INTRO

        self.story_save = StorySave()
        self.story_loader = StoryLoader()

        self.intro = StoryIntro(self.screen)
        self.stage_select = StoryStageSelect(
            self.screen,
            self.story_save,
            self.story_loader,
        )

        self.char_select = None
        self.story_scene = None
        self.battle = None

        self.chapter = None
        self.player_cls = None
        self.battle_num = 1
        self.ending_type = None

    # ─────────────────────────────────────────────
    # 외부 호출
    # ─────────────────────────────────────────────
    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                result = self._handle_escape()
                if result:
                    return result
                continue

            if self.state == StoryState.INTRO:
                result = self._handle_intro_event(event)
                if result:
                    return result

            elif self.state == StoryState.STAGE_SELECT:
                self._handle_stage_select_event(event)

            elif self.state == StoryState.CHAR_SELECT:
                self._handle_char_select_event(event)

            elif self.state == StoryState.SCENE:
                self._handle_story_scene_event(event)

            elif self.state == StoryState.BATTLE:
                result = self.battle.update([event])
                self._handle_battle_result(result)

            elif self.state == StoryState.WIN:
                self._handle_win_event(event)

            elif self.state == StoryState.LOSE:
                self._handle_lose_event(event)

            elif self.state == StoryState.ENDING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    return "back_to_menu"

        if self.state == StoryState.BATTLE:
            result = self.battle.update([])
            self._handle_battle_result(result)

        return None

    def draw(self):
        if self.state == StoryState.INTRO:
            self.intro.update()
            self.intro.draw()

        elif self.state == StoryState.STAGE_SELECT:
            self.stage_select.update()
            self.stage_select.draw()

        elif self.state == StoryState.CHAR_SELECT:
            if self.char_select:
                self.char_select.update()
                self.char_select.draw()

        elif self.state == StoryState.SCENE:
            if self.story_scene:
                self.story_scene.update()
                self.story_scene.draw()

        elif self.state == StoryState.BATTLE:
            if self.battle:
                self.battle.draw()

        elif self.state == StoryState.WIN:
            if self.battle:
                self.battle.draw()
            self._draw_story_result(win=True)

        elif self.state == StoryState.LOSE:
            if self.battle:
                self.battle.draw()
            self._draw_story_result(win=False)

        elif self.state == StoryState.ENDING:
            self._draw_ending()

    # ─────────────────────────────────────────────
    # ESC 처리
    # ─────────────────────────────────────────────
    def _handle_escape(self):
        if self.state == StoryState.INTRO:
            return "back_to_menu"

        if self.state == StoryState.STAGE_SELECT:
            self.intro = StoryIntro(self.screen)
            self.state = StoryState.INTRO
            return None

        if self.state in (
            StoryState.CHAR_SELECT,
            StoryState.SCENE,
            StoryState.BATTLE,
            StoryState.WIN,
            StoryState.LOSE,
        ):
            self._reset_stage_select()
            self.state = StoryState.STAGE_SELECT
            return None

        if self.state == StoryState.ENDING:
            return "back_to_menu"

        return None

    # ─────────────────────────────────────────────
    # INTRO
    # ─────────────────────────────────────────────
    def _handle_intro_event(self, event):
        self.intro.handle_event(event)

        if not self.intro.done:
            return None

        if self.intro.result == "back":
            return "back_to_menu"

        self._reset_stage_select()
        self.state = StoryState.STAGE_SELECT
        return None

    # ─────────────────────────────────────────────
    # STAGE SELECT
    # ─────────────────────────────────────────────
    def _handle_stage_select_event(self, event):
        self.stage_select.handle_event(event)

        if not self.stage_select.done:
            return

        ch = self.stage_select.result

        if ch is None:
            self.intro = StoryIntro(self.screen)
            self.state = StoryState.INTRO
            return

        self.chapter = ch
        self.char_select = CharacterSelect(self.screen)
        self.state = StoryState.CHAR_SELECT

    def _reset_stage_select(self):
        self.stage_select = StoryStageSelect(
            self.screen,
            self.story_save,
            self.story_loader,
        )

    # ─────────────────────────────────────────────
    # CHARACTER SELECT
    # ─────────────────────────────────────────────
    def _handle_char_select_event(self, event):
        self.char_select.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.char_select.done:
                cls_p1, _ = self.char_select.result
                self.player_cls = cls_p1

                if hasattr(cls_p1, "DISPLAY_NAME"):
                    self.story_save.set_character(cls_p1.DISPLAY_NAME)

                self._start_story_scene()

    # ─────────────────────────────────────────────
    # STORY SCENE
    # ─────────────────────────────────────────────
    def _start_story_scene(self):
        if self.chapter is None:
            self._reset_stage_select()
            self.state = StoryState.STAGE_SELECT
            return

        script_path = f"data/story/scripts/stage_{self.chapter['id']:02d}.json"

        self.story_scene = StoryScene(self.screen, script_path)
        self.battle_num = 1

        self.story_scene.script_data["_total_stages"] = self.story_loader.total
        self.story_scene.script_data["_current_stage"] = self.chapter["id"]

        self.state = StoryState.SCENE

    def _handle_story_scene_event(self, event):
        if self.story_scene is None:
            self._reset_stage_select()
            self.state = StoryState.STAGE_SELECT
            return

        self.story_scene.handle_event(event)

        if self.story_scene.done:
            self._handle_story_scene_result()

    def _handle_story_scene_result(self):
        result = self.story_scene.result

        if result == "battle":
            self.battle_num = 1
            self._start_story_battle()

        elif result == "battle_2":
            self.battle_num = 2
            self._start_story_battle()


        elif result == "end":

            if self.chapter is not None:
                self.story_save.mark_cleared(self.chapter["id"])
            self._go_next_chapter_or_stage_select()


        elif result and result.startswith("ending_"):
            self.ending_type = result.replace("ending_", "")
            self.state = StoryState.ENDING

        else:
            self._reset_stage_select()
            self.state = StoryState.STAGE_SELECT

    def _go_next_chapter_or_stage_select(self):
        if self.chapter is None:
            self._reset_stage_select()
            self.state = StoryState.STAGE_SELECT
            return

        next_id = None

        # 1순위: 현재 실행 중인 스토리 스크립트의 next_on_win / next
        if self.story_scene and hasattr(self.story_scene, "script_data"):
            next_id = (
                    self.story_scene.script_data.get("next_on_win")
                    or self.story_scene.script_data.get("next")
            )

        # 2순위: story_config.json의 chapter 정보
        if not next_id:
            next_id = self.chapter.get("next_on_win") or self.chapter.get("next")

        if next_id:
            if next_id == "ending":
                self.ending_type = "normal"
                self.state = StoryState.ENDING
                return

            try:
                next_num = int(str(next_id).split("_")[-1])
                next_ch = self.story_loader.get_chapter(next_num)
            except Exception:
                next_ch = None

            if next_ch:
                self.chapter = next_ch
                self._start_story_scene()
                return

        self._reset_stage_select()
        self.state = StoryState.STAGE_SELECT
    # ─────────────────────────────────────────────
    # BATTLE
    # ─────────────────────────────────────────────
    def _start_story_battle(self):
        if self.chapter is None or self.player_cls is None:
            self._reset_stage_select()
            self.state = StoryState.STAGE_SELECT
            return

        boss_cls = self.story_loader.get_boss_class(self.chapter)

        if boss_cls is None:
            from entities.characters.Einstein import Einstein
            boss_cls = Einstein

        self.battle = BattleSession(
            screen=self.screen,
            stage_info={
                "id": self.chapter["id"],
                "path": self.chapter["stage_json"],
            },
            player1_cls=self.player_cls,
            player2_cls=boss_cls,
            mode="story",
            player1_name="Player",
            player2_name=self.chapter.get("boss_name", "Boss"),
            player1_stocks=3,
            player2_stocks=self.chapter.get("boss_stocks", 3),
        )

        self.state = StoryState.BATTLE

    def _handle_battle_result(self, result):
        if result == "back":
            self._reset_stage_select()
            self.state = StoryState.STAGE_SELECT

        elif result == "p1_dead":
            self.state = StoryState.LOSE

        elif result == "p2_dead":
            if self.chapter is not None:
                self.story_save.mark_cleared(self.chapter["id"])
            self.state = StoryState.WIN

    # ─────────────────────────────────────────────
    # WIN / LOSE
    # ─────────────────────────────────────────────
    def _handle_win_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            if self.story_scene:
                self.story_scene.load_post_battle(self.battle_num)
                self.state = StoryState.SCENE
            else:
                self._reset_stage_select()
                self.state = StoryState.STAGE_SELECT

    def _handle_lose_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_RETURN, pygame.K_r):
            self._start_story_battle()

    # ─────────────────────────────────────────────
    # DRAW RESULT
    # ─────────────────────────────────────────────
    def _draw_story_result(self, win: bool):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        self.screen.blit(ov, (0, 0))

        fnt_big = font(52, bold=True)
        fnt_md = font(18, bold=True)
        fnt_sm = font(14)

        ch = self.chapter or {}

        if win:
            title_txt = f"Chapter {ch.get('id', '')}  CLEAR!"
            title_col = (100, 240, 130)
            sub_txt = ch.get("subtitle", "")
            hint_txt = "ENTER  next scene   |   ESC  stage select"
        else:
            title_txt = "DEFEATED"
            title_col = (240, 80, 80)
            sub_txt = "Don't give up. Try again!"
            hint_txt = "ENTER / R  retry   |   ESC  stage select"

        t = fnt_big.render(title_txt, True, title_col)
        self.screen.blit(
            t,
            (SCREEN_WIDTH // 2 - t.get_width() // 2, 220),
        )

        s = fnt_md.render(sub_txt, True, (200, 200, 220))
        self.screen.blit(
            s,
            (SCREEN_WIDTH // 2 - s.get_width() // 2, 290),
        )

        h = fnt_sm.render(hint_txt, True, (160, 160, 190))
        self.screen.blit(
            h,
            (SCREEN_WIDTH // 2 - h.get_width() // 2, 350),
        )

    # ─────────────────────────────────────────────
    # ENDING
    # ─────────────────────────────────────────────
    def _draw_ending(self):
        self.screen.fill((5, 6, 12))

        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        self.screen.blit(ov, (0, 0))

        etype = self.ending_type or "normal"

        fnt_big = font(46, bold=True)
        fnt_md = font(18, bold=True)
        fnt_sm = font(14)

        configs = {
            "null": {
                "title": "NULL  ENDING",
                "color": (200, 220, 255),
                "lines": [
                    "시간은 고쳐진 것이 아니라,",
                    "처음부터 고칠 필요가 없었다.",
                ],
            },
            "eternity": {
                "title": "ETERNITY  ENDING",
                "color": (255, 200, 100),
                "lines": [
                    "세계는 복구되었다.",
                    "그러나 벽 어딘가, 숫자 9가 새겨져 있다.",
                    "",
                    "TIME LOOP #9",
                ],
            },
            "normal": {
                "title": "NORMAL  ENDING",
                "color": (180, 255, 180),
                "lines": [
                    "계속된다...",
                ],
            },
        }

        cfg = configs.get(etype, configs["normal"])

        title = fnt_big.render(cfg["title"], True, cfg["color"])
        self.screen.blit(
            title,
            (SCREEN_WIDTH // 2 - title.get_width() // 2, 200),
        )

        for i, line in enumerate(cfg["lines"]):
            sf = fnt_md.render(line, True, (220, 220, 240))
            self.screen.blit(
                sf,
                (SCREEN_WIDTH // 2 - sf.get_width() // 2, 290 + i * 32),
            )

        hint = fnt_sm.render("ENTER  to return", True, (120, 120, 150))
        self.screen.blit(
            hint,
            (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 50),
        )