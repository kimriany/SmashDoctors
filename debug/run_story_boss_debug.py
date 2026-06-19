"""Start a story boss test battle with debug hotkeys.

Usage:
    python debug/run_story_boss_debug.py --boss einstein
    python debug/run_story_boss_debug.py --boss curie --stage 2
"""
from __future__ import annotations

import argparse

import pygame

from common import make_screen, run_game_object
from engine.battle_session import BattleSession
from entities.Boss_characters.cric_boss import CricBoss
from entities.Boss_characters.curie_boss import CurieBoss
from entities.Boss_characters.darwin_boss import DarwinBoss
from entities.Boss_characters.einstein_boss import EinsteinBoss
from entities.Boss_characters.hoking_boss import HokingBoss
from entities.Boss_characters.newton_boss import NewtonBoss
from entities.Boss_characters.ro2t_boss import Ro2tBoss
from entities.Boss_characters.schrodinger_boss import SchrodingerBoss
from entities.Boss_characters.turing_boss import TuringBoss
from entities.characters.StoryPlayer import StoryPlayer
from settings import SCREEN_WIDTH
from systems.font_manager import font


BOSSES = [
    ("crick", "Crick", "크릭", CricBoss),
    ("curie", "Curie", "퀴리", CurieBoss),
    ("darwin", "Darwin", "다윈", DarwinBoss),
    ("einstein", "Einstein", "아인슈타인", EinsteinBoss),
    ("hoking", "Hoking", "호킹", HokingBoss),
    ("newton", "Newton", "뉴턴", NewtonBoss),
    ("schrodinger", "Schrodinger", "슈뢰딩거", SchrodingerBoss),
    ("turing", "Turing", "Turing", TuringBoss),
    ("ro2t", "Ro2t", "Ro2t", Ro2tBoss),
]

BOSS_ALIASES = {
    "cric": "crick",
    "crick": "crick",
    "curie": "curie",
    "darwin": "darwin",
    "einstein": "einstein",
    "hawking": "hoking",
    "hoking": "hoking",
    "newton": "newton",
    "pita": "newton",
    "pythagoras": "newton",
    "schrodinger": "schrodinger",
    "schrödinger": "schrodinger",
    "turing": "turing",
    "root2": "ro2t",
    "ro2t": "ro2t",
}


def _boss_index_for(key: str) -> int:
    canonical = BOSS_ALIASES.get(key.strip().lower())
    if canonical is None:
        known = ", ".join(sorted(BOSS_ALIASES))
        raise SystemExit(f"Unknown boss '{key}'. Known: {known}")
    for idx, (boss_key, _label, _name, _cls) in enumerate(BOSSES):
        if boss_key == canonical:
            return idx
    raise SystemExit(f"Boss alias '{key}' resolved to missing key '{canonical}'")


class StoryBossDebugGame:
    def __init__(self, screen, boss_key: str, stage_id: int, q_skill: str, e_skill: str):
        self.screen = screen
        self.stage_id = stage_id
        self.q_skill = q_skill
        self.e_skill = e_skill
        self.boss_index = _boss_index_for(boss_key)
        self.show_help = True
        self.message = ""
        self.message_timer = 0
        self.battle = None
        self._make_battle()

    @property
    def boss_entry(self):
        return BOSSES[self.boss_index]

    def _make_battle(self):
        boss_key, boss_label, boss_name, boss_cls = self.boss_entry
        sid = f"stage_{self.stage_id:02d}"
        self.battle = BattleSession(
            screen=self.screen,
            stage_info={
                "id": sid,
                "path": f"data/stages/{sid}.json",
                "name": sid,
            },
            player1_cls=StoryPlayer,
            player2_cls=boss_cls,
            mode="story",
            player1_name="Hora",
            player2_name=boss_name,
            player1_stocks=99,
            player2_stocks=1,
            story_boss_profile={
                "class_path": f"{boss_cls.__module__}.{boss_cls.__name__}",
                "boss_name": boss_name,
                "debug_boss_key": boss_key,
            },
            story_player_skills={
                "skill_Q": self.q_skill,
                "skill_E": self.e_skill,
            },
        )
        self._set_message(f"Loaded {boss_label}")
        pygame.display.set_caption(f"SmashDoctors - Story Boss Debug: {boss_label}")

    def update(self, events):
        filtered_events = []
        for event in events:
            if event.type == pygame.KEYDOWN and self._handle_debug_key(event.key):
                continue
            filtered_events.append(event)

        if self.message_timer > 0:
            self.message_timer -= 1

        if self.battle.result is not None:
            return None

        result = self.battle.update(filtered_events)
        if result == "back":
            return "back"
        if result in ("p1_dead", "p2_dead"):
            self._set_message(f"Battle result: {result}  |  F2 resets")
        return None

    def draw(self):
        self.battle.draw()
        self._draw_overlay()

    def _handle_debug_key(self, key):
        if key == pygame.K_F1:
            self.show_help = not self.show_help
            return True
        if key == pygame.K_F2:
            self._make_battle()
            return True
        if key == pygame.K_F3:
            self._set_boss_hp_ratio(0.30)
            return True
        if key == pygame.K_F4:
            self._force_boss_domain()
            return True
        if key == pygame.K_F5:
            self._force_counter_domain()
            return True
        if key == pygame.K_F6:
            self._force_domain_break_and_finisher()
            return True
        if key == pygame.K_F7:
            self._heal_player()
            return True
        if key == pygame.K_F8:
            self._heal_boss()
            return True
        if key == pygame.K_F9:
            self._set_boss_ko_ready()
            return True
        if key in (pygame.K_LEFTBRACKET, pygame.K_PAGEUP):
            self._switch_boss(-1)
            return True
        if key in (pygame.K_RIGHTBRACKET, pygame.K_PAGEDOWN):
            self._switch_boss(1)
            return True

        if pygame.K_1 <= key <= pygame.K_9:
            idx = key - pygame.K_1
            if idx < len(BOSSES):
                self.boss_index = idx
                self._make_battle()
                return True
        return False

    def _switch_boss(self, delta):
        self.boss_index = (self.boss_index + delta) % len(BOSSES)
        self._make_battle()

    def _set_boss_hp_ratio(self, ratio):
        boss = self.battle.player2
        boss.hp = max(1.0, boss.max_hp * ratio)
        boss.damage_pct = (1.0 - boss.hp / max(1.0, boss.max_hp)) * 100.0
        boss.hit_flash = max(getattr(boss, "hit_flash", 0), 8)
        self._set_message(f"Boss HP set to {int(ratio * 100)}%")

    def _force_boss_domain(self):
        if not self.battle.boss_domain_started:
            self.battle._start_boss_domain()
        elif not getattr(self.battle.player2, "domain_active", False):
            self.battle.player2.open_domain(self.battle.event_bus)
        self._set_message("Boss domain forced")

    def _force_counter_domain(self):
        if not self.battle.boss_domain_started:
            self.battle._start_boss_domain()
        self.battle.domain_survive_timer = self.battle.domain_survive_required
        self.battle._unlock_player_domain()
        self._set_message("Counter domain ready. Press R")

    def _force_domain_break_and_finisher(self):
        if not self.battle.boss_domain_started:
            self.battle._start_boss_domain()
        if hasattr(self.battle.player2, "boss_domain_hp"):
            self.battle.player2.boss_domain_hp = 0.0
        self.battle._break_boss_domain()
        self.battle._force_player_finisher_ready()
        self._set_message("Boss domain broken. Finisher ready")

    def _heal_player(self):
        player = self.battle.player1
        player.hp = player.max_hp
        player.damage_pct = 0.0
        player.dead = False
        player.respawning = False
        player.stocks = max(getattr(player, "stocks", 0), 3)
        self._set_message("Player healed")

    def _heal_boss(self):
        boss = self.battle.player2
        boss.hp = boss.max_hp
        boss.damage_pct = 0.0
        boss.dead = False
        boss.stocks = 1
        boss.final_lock = bool(self.battle._story_domain_rule("final_lock", True))
        self._set_message("Boss healed")

    def _set_boss_ko_ready(self):
        boss = self.battle.player2
        boss.hp = 1.0
        boss.damage_pct = 100.0
        boss.final_lock = False
        boss.hit_flash = max(getattr(boss, "hit_flash", 0), 12)
        self._set_message("Boss HP 1, final lock released")

    def _set_message(self, text, frames=150):
        self.message = text
        self.message_timer = frames
        print(f"[story-boss-debug] {text}")

    def _draw_overlay(self):
        boss_key, boss_label, _boss_name, _boss_cls = self.boss_entry
        boss = self.battle.player2
        player = self.battle.player1

        panel_h = 122 if self.show_help else 56
        panel = pygame.Surface((SCREEN_WIDTH, panel_h), pygame.SRCALPHA)
        panel.fill((8, 10, 16, 178))
        self.screen.blit(panel, (0, 0))

        title_font = font(18, bold=True)
        small_font = font(13)
        hp = int(getattr(boss, "hp", 0))
        max_hp = int(getattr(boss, "max_hp", 1))
        p_hp = int(getattr(player, "hp", 0))
        p_max = int(getattr(player, "max_hp", 1))
        state = getattr(self.battle, "story_state", "-")
        domain_hp = int(getattr(boss, "boss_domain_hp", 0))
        domain_max = int(getattr(boss, "boss_domain_max_hp", 0))
        domain_active = "ON" if getattr(boss, "domain_active", False) else "off"
        finisher = "ready" if getattr(player, "finisher_ready", False) else "not ready"

        lines = [
            f"{self.boss_index + 1}/{len(BOSSES)} {boss_label} [{boss_key}]  Boss HP {hp}/{max_hp}  Player HP {p_hp}/{p_max}",
            f"State {state}  Boss domain {domain_active}  Domain HP {domain_hp}/{domain_max}  Finisher {finisher}",
        ]
        if self.show_help:
            lines.extend([
                "1-9 switch boss   [/] prev/next   F2 reset   F3 boss HP 30%   F4 boss domain",
                "F5 counter domain ready   F6 break domain + finisher   F7 heal player   F8 heal boss   F9 boss KO-ready   F1 help",
            ])
        if self.message_timer > 0 and self.message:
            lines.append(self.message)

        y = 10
        for i, line in enumerate(lines):
            surf = (title_font if i == 0 else small_font).render(line, True, (235, 245, 255))
            self.screen.blit(surf, (14, y))
            y += 24 if i == 0 else 20


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--boss", default="einstein", help="Boss key or alias. Use --list to print all.")
    parser.add_argument("--stage", type=int, default=1, choices=(1, 2, 3, 4))
    parser.add_argument("--q", default="hora_chrono", help="Story player Q skill id.")
    parser.add_argument("--e", default="hora_rift", help="Story player E skill id.")
    parser.add_argument("--list", action="store_true", help="Print boss keys and exit.")
    args = parser.parse_args()

    if args.list:
        for idx, (key, label, name, _cls) in enumerate(BOSSES, start=1):
            print(f"{idx}: {key:<12} {label:<12} {name}")
        return

    screen = make_screen("Story Boss Debug")
    game = StoryBossDebugGame(screen, args.boss, args.stage, args.q, args.e)
    run_game_object(game, "Story Boss Debug")


if __name__ == "__main__":
    main()
