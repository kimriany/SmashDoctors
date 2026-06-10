"""Start directly inside a battle.

Usage:
    python debug/run_battle.py --p1 curie --p2 hoking --stage 1
"""
from __future__ import annotations

import argparse

from common import run_game_object, make_screen
from debug.characters import get_character
from engine.battle_session import BattleSession


class BattleDebugGame:
    def __init__(self, screen, p1_cls, p2_cls, stage_id: int):
        sid = f"stage_{stage_id:02d}"
        self.battle = BattleSession(
            screen=screen,
            stage_info={
                "id": sid,
                "path": f"data/stages/{sid}.json",
                "name": sid,
            },
            player1_cls=p1_cls,
            player2_cls=p2_cls,
            mode="pvp",
            player1_name=getattr(p1_cls, "DISPLAY_NAME", "Player 1"),
            player2_name=getattr(p2_cls, "DISPLAY_NAME", "Player 2"),
            player1_stocks=3,
            player2_stocks=3,
        )

    def update(self, events):
        result = self.battle.update(events)
        if result in ("back", "p1_win", "p2_win"):
            print(f"[debug] battle result: {result}")
            return "back"
        return None

    def draw(self):
        self.battle.draw()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1", default="curie")
    parser.add_argument("--p2", default="hoking")
    parser.add_argument("--stage", type=int, default=1, choices=(1, 2, 3, 4))
    args = parser.parse_args()

    p1_cls = get_character(args.p1)
    p2_cls = get_character(args.p2)
    screen = make_screen(f"Battle {args.p1} vs {args.p2}")
    run_game_object(BattleDebugGame(screen, p1_cls, p2_cls, args.stage), "Battle Debug")


if __name__ == "__main__":
    main()
