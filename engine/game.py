# engine/game.py

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from scenes.mode_select import ModeSelect
from scenes.opening import Opening
from scenes.transition import Transition
from modes.pvp_game import PVPGame
from modes.story_game import StoryGame


class AppState:
    OPENING     = "opening"
    MODE_SELECT = "mode_select"
    PVP         = "pvp"
    STORY       = "story"


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        self.state = AppState.OPENING
        self.opening = Opening(self.screen)
        self.mode_select = ModeSelect(self.screen)
        self.current_game = None

    def _reset_mode_select(self):
        self.mode_select = ModeSelect(self.screen)
        self.current_game = None
        self.state = AppState.MODE_SELECT

    def run(self):
        while self.running:
            self.clock.tick(FPS)

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if not self.running:
                break

            if self.state == AppState.OPENING:
                self._update_opening(events)
                self.opening.draw()

            elif self.state == AppState.MODE_SELECT:
                self._update_mode_select(events)
                self.mode_select.update()
                self.mode_select.draw()

            elif self.state in (AppState.PVP, AppState.STORY):
                self._update_current_game(events)

            pygame.display.flip()

        pygame.quit()

    def _update_opening(self, events):
        for event in events:
            self.opening.handle_event(event)
        self.opening.update()
        if self.opening.done:
            self.state = AppState.MODE_SELECT

    def _update_mode_select(self, events):
        for event in events:
            self.mode_select.handle_event(event)

        if not self.mode_select.done:
            return

        result = self.mode_select.result

        if result == "pvp":
            self.current_game = PVPGame(self.screen)
            self.state = AppState.PVP

        elif result == "story":
            self.current_game = StoryGame(self.screen)
            self.state = AppState.STORY

        else:
            self._reset_mode_select()

    def _update_current_game(self, events):
        if self.current_game is None:
            self._reset_mode_select()
            return

        result = self.current_game.update(events)

        if result in ("back", "back_to_menu"):
            self._reset_mode_select()
            return

        if result == "quit":
            self.running = False
            return

        self.current_game.draw()