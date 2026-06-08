# modes/pvp_game.py

import pygame

from scenes.character_select import CharacterSelect
from scenes.stage_select import StageSelect
from engine.battle_session import BattleSession


class PVPState:
    CHAR_SELECT = "char_select"
    STAGE_SELECT = "stage_select"
    BATTLE = "battle"
    WIN = "win"


class PVPGame:
    def __init__(self, screen):
        self.screen = screen

        self.state = PVPState.CHAR_SELECT

        self.char_select = CharacterSelect(self.screen)
        self.stage_select = None
        self.battle = None

        self.cls_p1 = None
        self.cls_p2 = None
        self.stage_info = None

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "back_to_menu"

            if self.state == PVPState.CHAR_SELECT:
                self._handle_char_select_event(event)

            elif self.state == PVPState.STAGE_SELECT:
                self._handle_stage_select_event(event)

            elif self.state == PVPState.BATTLE:
                result = self.battle.update([event])
                if result == "back":
                    return "back_to_menu"

                if result in ("p1_win", "p2_win"):
                    self.state = PVPState.WIN

            elif self.state == PVPState.WIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    return "back_to_menu"

        if self.state == PVPState.BATTLE:
            result = self.battle.update([])
            if result == "back":
                return "back_to_menu"

            if result in ("p1_win", "p2_win"):
                self.state = PVPState.WIN

        return None

    def draw(self):
        if self.state == PVPState.CHAR_SELECT:
            self.char_select.update()
            self.char_select.draw()

        elif self.state == PVPState.STAGE_SELECT:
            self.stage_select.update()
            self.stage_select.draw()

        elif self.state == PVPState.BATTLE:
            self.battle.draw()

        elif self.state == PVPState.WIN:
            self.battle.draw_win()

    def _handle_char_select_event(self, event):
        self.char_select.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.char_select.done:
                self.cls_p1, self.cls_p2 = self.char_select.result
                self.stage_select = StageSelect(self.screen)
                self.state = PVPState.STAGE_SELECT

    def _handle_stage_select_event(self, event):
        self.stage_select.handle_event(event)

        if self.stage_select.done:
            self.stage_info = self.stage_select.result

            self.battle = BattleSession(
                screen=self.screen,
                stage_info=self.stage_info,
                player1_cls=self.cls_p1,
                player2_cls=self.cls_p2,
                mode="pvp",
                player1_name="Player 1",
                player2_name="Player 2",
                player1_stocks=3,
                player2_stocks=3,
            )

            self.state = PVPState.BATTLE