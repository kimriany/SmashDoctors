"""
Pythagoras (Pita) — 기하와 벡터로 빠르게 각을 만드는 러시형 캐릭터.

일반 스킬:
  Q / ;  Vector Dash       — 삼각 궤적을 남기는 전진 대시
  E / '  Right-Angle Bolt  — 직각 삼각형 형태의 관통 광선
  R / /  Pythagorean Domain

영역 전개 중 강화 스킬:
  Q / ;  Hypotenuse Rush   — 더 길고 강한 대시
  E / '  Theorem Ray       — 더 넓은 정리 광선
"""
from entities.player import Player
from systems.skill import BeamSkill, DashSkill, DomainUltimateSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


def _triangle_points(cx, cy, size, facing):
    return [
        (cx + facing * size, cy),
        (cx - facing * size * 0.45, cy - size * 0.62),
        (cx - facing * size * 0.45, cy + size * 0.62),
    ]


class VectorDash(_NormalOnlyMixin, DashSkill):
    DISPLAY_NAME = "Vector Dash"
    DESCRIPTION = "Dash forward with a geometric trail."
    DASH_SPEED = 21.0
    DASH_FRAMES = 10
    DASH_DAMAGE = 13
    TRAIL_COLOR = (95, 185, 255)
    COOLDOWN_SEC = 2.2

    def __init__(self):
        super().__init__("Vector Dash", damage=13, cooldown=132, duration=16)
        self.charge_value = 0.85

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        if psys:
            for _ in range(7):
                psys.spawn(owner.rect.centerx, owner.rect.centery,
                           random.choice([(95, 185, 255), (230, 250, 255), (75, 120, 255)]),
                           count=1, speed=random.uniform(3, 7), life=random.randint(10, 18), r=3)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        return pygame.Rect(owner.rect.x - 18, owner.rect.y + 2, owner.rect.w + 36, owner.rect.h - 4)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        super().draw_behind(owner, screen, camera, dr, bob, z)
        if not self.active:
            return
        t = self.timer / max(1, self.duration)
        for i in range(5):
            size = int((16 + i * 5) * z)
            cx = dr.centerx - owner.facing * int((28 + i * 22) * z)
            cy = dr.centery + bob
            alpha = max(0, int(145 * t) - i * 20)
            sf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            pts = _triangle_points(size * 1.5, size * 1.5, size, owner.facing)
            pygame.draw.polygon(sf, (80, 170, 255, alpha // 3), pts)
            pygame.draw.polygon(sf, (230, 250, 255, alpha), pts, max(1, int(2 * z)))
            screen.blit(sf, (cx - size * 1.5, cy - size * 1.5))

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x += owner.facing * 7
        target.vel.y -= 3
        super().on_hit(owner, target, event_bus, psys, fsys)


class RightAngleBolt(_NormalOnlyMixin, BeamSkill):
    DISPLAY_NAME = "Right-Angle Bolt"
    DESCRIPTION = "Fire a piercing beam shaped by a right triangle."
    BEAM_LENGTH = 315
    BEAM_WIDTH = 24
    BEAM_COLOR = (80, 175, 255)
    BEAM_GLOW = (225, 250, 255)
    COOLDOWN_SEC = 5.4

    def __init__(self):
        super().__init__("Right-Angle Bolt", damage=24, cooldown=324, duration=23)
        self.charge_value = 1.15

    def draw_front(self, owner, screen, camera, dr, bob, z):
        super().draw_front(owner, screen, camera, dr, bob, z)
        if not self.active:
            return
        t = self.timer / max(1, self.duration)
        alpha = max(0, int(210 * t))
        length = int(self.BEAM_LENGTH * z)
        height = int((self.BEAM_WIDTH + 64) * z)
        sx = dr.right - int(6 * z) if owner.facing == 1 else dr.left - length + int(6 * z)
        sy = dr.centery + bob - height // 2
        sf = pygame.Surface((length, height), pygame.SRCALPHA)
        if owner.facing == 1:
            pts = [(0, height // 2), (length, height // 2), (length, height // 2 - int(52 * z))]
            tick_dir = 1
        else:
            pts = [(length, height // 2), (0, height // 2), (0, height // 2 - int(52 * z))]
            tick_dir = -1
        pygame.draw.polygon(sf, (80, 175, 255, alpha // 5), pts)
        pygame.draw.lines(sf, (235, 250, 255, alpha), False, pts, max(2, int(3 * z)))
        for i in range(4):
            x = int((i + 1) * length / 5)
            top = height // 2 - int((18 + i * 4) * z)
            bot = height // 2 + int((10 + i * 3) * z)
            pygame.draw.line(sf, (120, 210, 255, alpha // 2), (x, top), (x + tick_dir * int(18 * z), bot), max(1, int(2 * z)))
        screen.blit(sf, (sx, sy))


class PitaDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Pythagorean Domain"
    DESCRIPTION = "Open Pythagoras' theorem domain."
    DOMAIN_BG_PATH = "assets/images/charactor/pita/domain.jpeg"
    DOMAIN_PARTICLE_COLOR = (95, 185, 255)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 30
    CUTSCENE_ZOOM = 1.48
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Pythagorean Domain", damage=0, duration=999999)


class HypotenuseRush(_DomainOnlyMixin, VectorDash):
    DISPLAY_NAME = "Hypotenuse Rush"
    DESCRIPTION = "Domain skill - longer vector dash with stronger launch."
    DASH_SPEED = 27.0
    DASH_FRAMES = 12
    DASH_DAMAGE = 26
    TRAIL_COLOR = (255, 235, 120)
    COOLDOWN_SEC = 3.2

    def __init__(self):
        DashSkill.__init__(self, "Hypotenuse Rush", damage=26, cooldown=192, duration=18)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.55

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x += owner.facing * 12
        target.vel.y -= 5
        super().on_hit(owner, target, event_bus, psys, fsys)


class TheoremRay(_DomainOnlyMixin, RightAngleBolt):
    DISPLAY_NAME = "Theorem Ray"
    DESCRIPTION = "Domain skill - draws the theorem as a wide cutting ray."
    BEAM_LENGTH = 390
    BEAM_WIDTH = 36
    BEAM_COLOR = (255, 215, 95)
    BEAM_GLOW = (255, 250, 215)
    COOLDOWN_SEC = 6.2

    def __init__(self):
        BeamSkill.__init__(self, "Theorem Ray", damage=39, cooldown=372, duration=28)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.85

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x += owner.facing * 9
        target.vel.y -= 4
        super().on_hit(owner, target, event_bus, psys, fsys)


class Pita(Player):
    WEIGHT = 92
    KB_GROWTH = 85
    BASE_KB = 28
    WALK_SPEED = 7.2
    JUMP_POWER = -16.0
    MAX_JUMPS = 2
    ATTACK_DMG = 11
    ATK_FRAMES = 18
    ATK_CD = 30
    HIT_START = 3
    HIT_END = 14

    BODY_COLOR = (55, 130, 230)
    TRIM_COLOR = (25, 65, 155)
    GLOW_COLOR = (110, 185, 255)
    DARK_COLOR = (20, 45, 110)
    DISPLAY_NAME = "Pythagoras"
    DESCRIPTION = "Fast geometric fighter.\nBuilds angles with dash and beam skills."
    PREVIEW_COLOR = (55, 130, 230)
    SKILL_NAME = "Vector Dash"

    SPRITE_PATH = "assets/images/charactor/pita/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/pita/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/pita/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/pita/attack.png"
    SPRITE_SKILL = "assets/images/charactor/pita/skill.png"

    SPRITE_SCALE = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Vector Dash", "DashSkill", 13, 24, 2.2),
        "cc": ("Right-Angle Bolt", "BeamSkill", 24, 32, 5.4),
        "enhance": ("Pythagorean Domain", "DomainUltimateSkill", 0, 0, 0.0),
    }

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR
        self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR
        self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"] = VectorDash()
        self.skills["skill_E"] = RightAngleBolt()
        self.skills["skill_R"] = PitaDomain()
        self.skills["skill_Q_domain"] = HypotenuseRush()
        self.skills["skill_E_domain"] = TheoremRay()

    def use_skill(self, skill_key: str, event_bus=None, psys=None) -> bool:
        domain_key = skill_key + "_domain"
        if domain_key in self.skills:
            domain_skill = self.skills[domain_key]
            if domain_skill.can_use(self):
                domain_skill.use(self, event_bus, psys)
                self.active_skill = domain_skill
                return True

        skill = self.skills.get(skill_key)
        if skill and skill.can_use(self):
            skill.use(self, event_bus, psys)
            self.active_skill = skill
            return True

        return False

    def get_char_name(self):
        return "Pythagoras"
