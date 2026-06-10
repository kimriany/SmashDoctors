"""Debug launch helpers for jumping directly into scenes/modes."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE


def make_screen(title_suffix: str = "Debug"):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"{TITLE} - {title_suffix}")
    return screen


def run_game_object(game, title_suffix: str = "Debug"):
    pygame.display.set_caption(f"{TITLE} - {title_suffix}")
    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(FPS)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        if not running:
            break

        result = game.update(events)
        if result in ("quit", "back", "back_to_menu"):
            running = False
            continue

        game.draw()
        pygame.display.flip()

    pygame.quit()


def run_scene(scene, title_suffix: str = "Scene Debug"):
    pygame.display.set_caption(f"{TITLE} - {title_suffix}")
    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(FPS)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif hasattr(scene, "handle_event"):
                scene.handle_event(event)

        if hasattr(scene, "update"):
            scene.update()
        if hasattr(scene, "draw"):
            scene.draw()

        if getattr(scene, "done", False):
            print(f"[debug] scene done: result={getattr(scene, 'result', None)}")

        pygame.display.flip()

    pygame.quit()
