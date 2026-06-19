"""Start the final Future Hora boss debugger directly.

Usage:
    python debug/run_hora_debug.py
    python debug/run_hora_debug.py --stage 4
"""
from __future__ import annotations

import argparse

from common import make_screen, run_game_object
from run_story_boss_debug import StoryBossDebugGame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, default=4, choices=(1, 2, 3, 4))
    parser.add_argument("--q", default="hora_chrono", help="Story player Q skill id.")
    parser.add_argument("--e", default="hora_rift", help="Story player E skill id.")
    args = parser.parse_args()

    screen = make_screen("Hora Boss Debug")
    game = StoryBossDebugGame(screen, "hora", args.stage, args.q, args.e)
    run_game_object(game, "Hora Boss Debug")


if __name__ == "__main__":
    main()
