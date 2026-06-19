from entities.player import Player
from systems.skill import BeamSkill, DomainUltimateSkill, ProjectileSkill, SummonZoneSkill
import math
import random

import pygame

from entities.characters.Einstein import GravityLash, EventHorizon
from entities.characters.Curie import RadiumShard, RadiationField
from entities.characters.Nobel import BouncingBomb, MegaBombDrop
from entities.characters.Pita import DecisiveStrike, JudgementSpin
from entities.characters.Turing import HackVirus, HaltingProblem
from entities.characters.Hoking import HawkingShard, TimeDilation
from entities.characters.Schrödinger import CatBox, QuantumLeap


class StoryPulse(ProjectileSkill):
    DISPLAY_NAME = "Chrono Shard"
    DESCRIPTION = "Fire a bright time shard forward."
    COOLDOWN_SEC = 3.2
    PROJ_SPEED = 13.5
    PROJ_SIZE = 20
    PROJ_COLOR = (90, 205, 255)
    PROJ_GLOW = (180, 240, 255)

    def __init__(self):
        super().__init__("Chrono Shard", damage=34, cooldown=190, duration=82)
        self.charge_value = 1.45
        self.finisher_charge_value = 1.15
        self._trail = []

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        self._trail = []
        if psys:
            psys.spawn(owner.rect.centerx, owner.rect.centery, self.PROJ_GLOW, count=16, speed=4, life=18, r=4, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        super().on_update(owner, event_bus, psys)
        if getattr(self, "_alive", False):
            self._trail.append((self._px, self._py, 18))
            self._trail = [(x, y, life - 1) for x, y, life in self._trail if life > 1][-10:]
            if psys and self.timer % 4 == 0:
                psys.spawn(self._px, self._py, random.choice([self.PROJ_COLOR, self.PROJ_GLOW]), count=2, speed=1.8, gravity=-0.02, life=12, r=3, glow=True)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        for x, y, life in self._trail:
            sx, sy = camera.world_to_screen(x, y)
            rr = max(3, int((life / 18) * self.PROJ_SIZE * z))
            sf = pygame.Surface((rr * 4, rr * 4), pygame.SRCALPHA)
            pygame.draw.circle(sf, (*self.PROJ_COLOR, int(78 * life / 18)), (rr * 2, rr * 2), rr * 2)
            screen.blit(sf, (sx - rr * 2, sy - rr * 2))
        super().draw_front(owner, screen, camera, dr, bob, z)


class StoryAnchor(SummonZoneSkill):
    DISPLAY_NAME = "Causality Rift"
    DESCRIPTION = "Warn, then rupture the target area."
    COOLDOWN_SEC = 5.6
    WARN_FRAMES = 30
    ZONE_W = 168
    ZONE_H = 112
    ZONE_COLOR = (95, 225, 190)
    ZONE_GLOW = (180, 255, 230)

    def __init__(self):
        super().__init__("Causality Rift", damage=46, cooldown=335, duration=72)
        self.charge_value = 1.75
        self.finisher_charge_value = 1.45

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        else:
            super().on_start(owner, event_bus, psys)
        if psys:
            psys.spawn(self._zone_x, self._zone_y - self.ZONE_H * 0.5, self.ZONE_GLOW, count=18, speed=3.5, gravity=-0.04, life=22, r=4, glow=True)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        super().draw_behind(owner, screen, camera, dr, bob, z)
        if not self.active:
            return
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H * 0.45
        sx, sy = camera.world_to_screen(zx, zy)
        elapsed = self.duration - self.timer
        for i in range(4):
            pulse = (elapsed * 0.055 + i * 0.25) % 1.0
            rx = int((self.ZONE_W * (0.18 + pulse * 0.56)) * z)
            ry = int((self.ZONE_H * (0.14 + pulse * 0.42)) * z)
            alpha = int(110 * (1.0 - pulse))
            pygame.draw.ellipse(screen, (*self.ZONE_GLOW, alpha), (sx - rx, sy - ry, rx * 2, ry * 2), max(1, int(2 * z)))


class StoryDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Counter Domain"
    DESCRIPTION = "Answer the boss domain."
    DOMAIN_BG_PATH = "assets/images/charactor/Hora/hora_domain.png"
    DOMAIN_PARTICLE_COLOR = (80, 220, 255)
    BREAK_HITS = 999
    CUTSCENE_FRAMES = 38
    CUTSCENE_ZOOM = 1.48
    TRANSITION_SPEED = 0.04

    def __init__(self):
        super().__init__("Counter Domain")


class DomainPulse(BeamSkill):
    DISPLAY_NAME = "Domain Rend"
    DESCRIPTION = "A reinforced beam that cracks domains."
    COOLDOWN_SEC = 2.6
    BEAM_LENGTH = 420
    BEAM_WIDTH = 42
    BEAM_COLOR = (100, 235, 255)
    BEAM_GLOW = (220, 255, 255)

    def __init__(self):
        super().__init__("Domain Rend", damage=64, cooldown=155, duration=34)
        self.charge_value = 0.0
        self.finisher_charge_value = 2.1

    def on_start(self, owner, event_bus=None, psys=None):
        if psys:
            px = owner.rect.centerx + owner.facing * 70
            py = owner.rect.centery
            psys.spawn(px, py, self.BEAM_GLOW, count=28, speed=5, life=26, r=5, glow=True)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        super().draw_front(owner, screen, camera, dr, bob, z)
        if not self.active:
            return
        t = self.timer / max(1, self.duration)
        cx = dr.centerx + owner.facing * int(110 * z)
        cy = dr.centery + bob
        for i in range(5):
            r = int((28 + i * 15 + (1.0 - t) * 22) * z)
            alpha = int((95 - i * 12) * t)
            pygame.draw.circle(screen, (*self.BEAM_GLOW, alpha), (cx, cy), max(3, r), max(1, int(2 * z)))


class DomainAnchor(SummonZoneSkill):
    DISPLAY_NAME = "Paradox Bloom"
    DESCRIPTION = "A widened rupture inside your domain."
    COOLDOWN_SEC = 4.4
    WARN_FRAMES = 24
    ZONE_W = 220
    ZONE_H = 142
    ZONE_COLOR = (105, 245, 215)
    ZONE_GLOW = (225, 255, 245)

    def __init__(self):
        super().__init__("Paradox Bloom", damage=72, cooldown=265, duration=70)
        self.charge_value = 0.0
        self.finisher_charge_value = 2.8

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        else:
            super().on_start(owner, event_bus, psys)
        if psys:
            for col in (self.ZONE_GLOW, self.ZONE_COLOR, (255, 245, 150)):
                psys.spawn(self._zone_x, self._zone_y - self.ZONE_H * 0.4, col, count=14, speed=4.2, gravity=-0.05, life=24, r=4, glow=True)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        super().draw_behind(owner, screen, camera, dr, bob, z)
        if not self.active:
            return
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H * 0.5
        sx, sy = camera.world_to_screen(zx, zy)
        elapsed = self.duration - self.timer
        for i in range(8):
            ang = elapsed * 0.08 + i * math.tau / 8
            px = sx + math.cos(ang) * self.ZONE_W * 0.34 * z
            py = sy + math.sin(ang) * self.ZONE_H * 0.22 * z
            rr = max(3, int(8 * z))
            pygame.draw.circle(screen, (*self.ZONE_GLOW, 120), (int(px), int(py)), rr)


class StoryPlayer(Player):
    DISPLAY_NAME = "Hora"
    DESCRIPTION = "Default story-mode combatant."
    PREVIEW_COLOR = (95, 205, 255)
    SKILL_NAME = "Chrono Shard"

    BODY_COLOR = (76, 154, 210)
    TRIM_COLOR = (28, 56, 98)
    GLOW_COLOR = (95, 220, 255)
    DARK_COLOR = (8, 22, 44)

    SPRITE_PATH = "assets/images/charactor/Main_character/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Main_character/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Main_character/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Main_character/attack.png"
    SPRITE_SKILL = "assets/images/charactor/Main_character/attack.png"
    SPRITE_SCALE = 1.34
    SPRITE_SCALE_X = 1.48
    SPRITE_OFFSET_Y = 2

    WALK_SPEED = 6.8
    JUMP_POWER = -15.8
    ATTACK_DMG = 15

    Q_SKILL_OPTIONS = [
        {
            "id": "hora_chrono",
            "source": "Hora",
            "name": "Chrono Shard",
            "desc": "Fast projectile with a bright trail.",
            "class": StoryPulse,
        },
        {
            "id": "einstein_gravity",
            "source": "Einstein",
            "name": "Gravity Lash",
            "desc": "Hook projectile that pulls the target.",
            "class": GravityLash,
        },
        {
            "id": "curie_radium",
            "source": "Curie",
            "name": "Radium Shard",
            "desc": "Radioactive projectile pressure.",
            "class": RadiumShard,
        },
        {
            "id": "nobel_bomb",
            "source": "Nobel",
            "name": "Bouncing Bomb",
            "desc": "Explosive bouncing projectile.",
            "class": BouncingBomb,
        },
        {
            "id": "schrodinger_box",
            "source": "Schrodinger",
            "name": "Cat's Box",
            "desc": "Trap and disturb the target.",
            "class": CatBox,
        },
        {
            "id": "turing_hack",
            "source": "Turing",
            "name": "Hack Virus",
            "desc": "Forward hacking burst.",
            "class": HackVirus,
        },
        {
            "id": "hoking_shard",
            "source": "Hoking",
            "name": "Hawking Shard",
            "desc": "Long-range cosmic projectile.",
            "class": HawkingShard,
        },
        {
            "id": "pita_strike",
            "source": "Pythagoras",
            "name": "Decisive Strike",
            "desc": "Close-range geometry strike.",
            "class": DecisiveStrike,
        },
    ]

    E_SKILL_OPTIONS = [
        {
            "id": "hora_rift",
            "source": "Hora",
            "name": "Causality Rift",
            "desc": "Large warning field eruption.",
            "class": StoryAnchor,
        },
        {
            "id": "einstein_horizon",
            "source": "Einstein",
            "name": "Event Horizon",
            "desc": "Black-hole zone that pulls and bursts.",
            "class": EventHorizon,
        },
        {
            "id": "curie_field",
            "source": "Curie",
            "name": "Radiation Field",
            "desc": "Persistent radioactive field.",
            "class": RadiationField,
        },
        {
            "id": "nobel_drop",
            "source": "Nobel",
            "name": "Mega Bomb Drop",
            "desc": "Heavy delayed explosion zone.",
            "class": MegaBombDrop,
        },
        {
            "id": "schrodinger_leap",
            "source": "Schrodinger",
            "name": "Quantum Leap",
            "desc": "Quantum movement and pressure.",
            "class": QuantumLeap,
        },
        {
            "id": "turing_halting",
            "source": "Turing",
            "name": "Halting Problem",
            "desc": "Grid trap with delayed burst.",
            "class": HaltingProblem,
        },
        {
            "id": "hoking_time",
            "source": "Hoking",
            "name": "Time Dilation",
            "desc": "Slow field with cosmic pressure.",
            "class": TimeDilation,
        },
        {
            "id": "pita_spin",
            "source": "Pythagoras",
            "name": "Judgement Spin",
            "desc": "Spinning geometry attack.",
            "class": JudgementSpin,
        },
    ]

    def _init_skills(self):
        self.skills["skill_Q"] = StoryPulse()
        self.skills["skill_E"] = StoryAnchor()
        self.skills["skill_R"] = StoryDomain()
        self.skills["skill_Q_domain"] = DomainPulse()
        self.skills["skill_E_domain"] = DomainAnchor()

    @classmethod
    def get_story_skill_options(cls, slot):
        if slot == "skill_Q":
            return cls.Q_SKILL_OPTIONS
        if slot == "skill_E":
            return cls.E_SKILL_OPTIONS
        return []

    @classmethod
    def _skill_class_for_id(cls, slot, skill_id):
        for option in cls.get_story_skill_options(slot):
            if option["id"] == skill_id:
                return option["class"]
        return None

    def configure_story_skills(self, loadout):
        loadout = loadout or {}

        q_cls = self._skill_class_for_id("skill_Q", loadout.get("skill_Q")) or StoryPulse
        e_cls = self._skill_class_for_id("skill_E", loadout.get("skill_E")) or StoryAnchor

        self.skills["skill_Q"] = q_cls()
        self.skills["skill_E"] = e_cls()

        self.selected_story_loadout = {
            "skill_Q": loadout.get("skill_Q", "hora_chrono"),
            "skill_E": loadout.get("skill_E", "hora_rift"),
        }

    def get_char_name(self):
        return self.DISPLAY_NAME
