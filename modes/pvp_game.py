# modes/pvp_game.py
import pygame
import os

from scenes.character_select import CharacterSelect
from scenes.stage_select import StageSelect
from scenes.battle_intro import BattleIntro
from scenes.transition import Transition
from engine.battle_session import BattleSession


class PVPState:
    CHAR_SELECT   = "char_select"
    STAGE_SELECT  = "stage_select"
    BATTLE_INTRO  = "battle_intro"   # VS + 카운트다운
    BATTLE        = "battle"
    WIN           = "win"


class PVPGame:
    def __init__(self, screen):
        self.screen = screen

        self.state       = PVPState.CHAR_SELECT
        self.char_select = CharacterSelect(self.screen)
        self.stage_select = None
        self.battle_intro = None
        self.battle       = None

        self.cls_p1    = None
        self.cls_p2    = None
        self.stage_info = None

        # char → stage 전환
        self._cs_transition = Transition("wipe", duration=30)

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.state in (PVPState.BATTLE, PVPState.WIN,
                                  PVPState.BATTLE_INTRO):
                    return "back_to_menu"
                if self.state == PVPState.STAGE_SELECT:
                    # 캐릭터 선택으로 돌아가기
                    self.char_select = CharacterSelect(self.screen)
                    self.state = PVPState.CHAR_SELECT
                    return None
                return "back_to_menu"

            if self.state == PVPState.CHAR_SELECT:
                self._handle_char_select(event)

            elif self.state == PVPState.STAGE_SELECT:
                self._handle_stage_select(event)

            elif self.state == PVPState.BATTLE_INTRO:
                self.battle_intro.handle_event(event)

            elif self.state == PVPState.BATTLE:
                result = self.battle.update([event])
                self._process_battle_result(result)

            elif self.state == PVPState.WIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    return "back_to_menu"

        # BATTLE_INTRO 업데이트
        if self.state == PVPState.BATTLE_INTRO:
            self.battle_intro.update()
            if self.battle_intro.done:
                self.state = PVPState.BATTLE

        # BATTLE 프레임 업데이트
        if self.state == PVPState.BATTLE:
            result = self.battle.update([])
            self._process_battle_result(result)

        return None

    def draw(self):
        if self.state == PVPState.CHAR_SELECT:
            self.char_select.update()
            self.char_select.draw()

        elif self.state == PVPState.STAGE_SELECT:
            self.stage_select.update()
            self.stage_select.draw()

        elif self.state == PVPState.BATTLE_INTRO:
            self.battle_intro.draw()

        elif self.state == PVPState.BATTLE:
            self.battle.draw()

        elif self.state == PVPState.WIN:
            self.battle.draw_win()

    # ─── 캐릭터 선택 ───────────────────────────────────────────
    def _handle_char_select(self, event):
        self.char_select.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.char_select.done and not self.char_select.transition.active:
                self.cls_p1, self.cls_p2 = self.char_select.result
                self.stage_select = StageSelect(self.screen)
                self.state = PVPState.STAGE_SELECT

    # ─── 스테이지 선택 ─────────────────────────────────────────
    def _handle_stage_select(self, event):
        self.stage_select.handle_event(event)
        transition_active = getattr(self.stage_select, "transition", None)
        transition_active = transition_active.active if transition_active else False
        if self.stage_select.done and not transition_active:
            self.stage_info = self.stage_select.result
            self._start_battle_intro()

    # ─── 배틀 인트로 ───────────────────────────────────────────
    def _start_battle_intro(self):
        # 배경 이미지 로드
        sid   = self.stage_info.get("id","")
        bg_sf = None
        for ext in [".png",".jpg",".jpeg"]:
            p = f"assets/images/bg_{sid}{ext}"
            if os.path.exists(p):
                try:
                    import pygame as pg
                    raw = pg.image.load(p).convert()
                    W,H = self.screen.get_size()
                    bg_sf = pg.transform.smoothscale(raw,(W,H))
                    break
                except Exception:
                    pass

        p1 = self.cls_p1
        p2 = self.cls_p2

        self.battle_intro = BattleIntro(
            screen     = self.screen,
            stage_name = self.stage_info.get("name","Stage"),
            stage_bg   = bg_sf,
            p1_name    = getattr(p1,"DISPLAY_NAME","Player 1"),
            p1_color   = getattr(p1,"GLOW_COLOR",  (110,185,255)),
            p2_name    = getattr(p2,"DISPLAY_NAME","Player 2"),
            p2_color   = getattr(p2,"GLOW_COLOR",  (255,130,110)),
        )
        self.state = PVPState.BATTLE_INTRO

        # BattleSession은 인트로와 동시에 미리 초기화 (로딩 시간 숨김)
        self.battle = BattleSession(
            screen         = self.screen,
            stage_info     = self.stage_info,
            player1_cls    = self.cls_p1,
            player2_cls    = self.cls_p2,
            mode           = "pvp",
            player1_name   = getattr(self.cls_p1,"DISPLAY_NAME","Player 1"),
            player2_name   = getattr(self.cls_p2,"DISPLAY_NAME","Player 2"),
            player1_stocks = 3,
            player2_stocks = 3,
        )

    # ─── 전투 결과 ─────────────────────────────────────────────
    def _process_battle_result(self, result):
        if result is None:
            return
        if result == "back":
            # 이미 ESC 처리됨
            pass
        elif result in ("p1_win","p2_win"):
            self.state = PVPState.WIN