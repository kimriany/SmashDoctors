"""
Turing — 비트스트림과 계산 영역으로 상대 움직임을 제어하는 캐릭터.

일반 스킬:
  Q / ;  Bitstream Pulse  — 이진 파동 투사체
  E / '  Halting Field    — 격자 구역, 내부 적 감속
  R / /  Turing Domain

영역 전개 중 강화 스킬:
  Q / ;  Universal Tape   — 빠르고 큰 계산 투사체
  E / '  Decidability Trap — 다단히트 정지 문제 격자
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


def _clamp_alpha(v):
    return max(0, min(255, int(v)))


class BitstreamPulse(_NormalOnlyMixin, ProjectileSkill):
    DISPLAY_NAME = "Bitstream Pulse"
    DESCRIPTION = "Launch a compact binary pulse."
    PROJ_SPEED = 10.5
    PROJ_SIZE = 18
    PROJ_COLOR = (80, 235, 190)
    PROJ_GLOW = (120, 200, 255)
    COOLDOWN_SEC = 4.0

    def __init__(self):
        super().__init__("Bitstream Pulse", damage=22, cooldown=240, duration=76)
        self.charge_value = 1.0
        self._spin = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        self._px = float(owner.rect.centerx + owner.facing * 28)
        self._py = float(owner.rect.centery - 4)
        self._vx = self.PROJ_SPEED * owner.facing
        self._alive = True
        self._spin = 0.0
        if psys:
            psys.spawn(owner.rect.centerx, owner.rect.centery, self.PROJ_COLOR, count=6, speed=3, life=16, r=3)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive:
            return
        self._px += self._vx
        self._spin += 0.35
        self._py += math.sin(self._spin) * 0.55
        if psys and self.timer % 4 == 0:
            psys.spawn(int(self._px - owner.facing * 12), int(self._py),
                       random.choice([(80, 235, 190), (60, 140, 255), (210, 250, 255)]),
                       count=1, speed=1.4, life=14, r=2)
        if abs(self._px - owner.rect.centerx) > 820:
            self._alive = False

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active or not getattr(self, "_alive", False):
            return
        sx, sy = camera.world_to_screen(self._px, self._py)
        r = max(5, int(self.PROJ_SIZE * z))
        sf = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
        cx = cy = r * 2.5
        pygame.draw.circle(sf, (*self.PROJ_GLOW, 70), (int(cx), int(cy)), r * 2)
        pygame.draw.circle(sf, (*self.PROJ_COLOR, 210), (int(cx), int(cy)), r)
        for i in range(8):
            ang = self._spin + i * math.tau / 8
            x = cx + math.cos(ang) * r * 1.55
            y = cy + math.sin(ang) * r * 1.55
            col = (210, 250, 255, 190) if i % 2 == 0 else (40, 120, 255, 180)
            pygame.draw.rect(sf, col, (int(x) - 2, int(y) - 2, max(3, int(5 * z)), max(3, int(5 * z))))
        screen.blit(sf, (sx - int(cx), sy - int(cy)))

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._alive = False
        target.vel.x += owner.facing * 6
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.PROJ_GLOW, count=18, speed=5, life=22, r=4)
        super().on_hit(owner, target, event_bus, psys, fsys)


class HaltingField(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Halting Field"
    DESCRIPTION = "Summon a computation grid that slows enemies."
    WARN_FRAMES = 28
    ZONE_W = 175
    ZONE_H = 105
    ZONE_COLOR = (55, 185, 165)
    ZONE_GLOW = (120, 220, 255)
    COOLDOWN_SEC = 8.0
    SLOW_FACTOR = 0.52

    def __init__(self):
        super().__init__("Halting Field", damage=18, cooldown=480, duration=104)
        self.charge_value = 1.25

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx - owner.rect.centerx) < 430:
            self._zone_x = target.rect.centerx
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 215
        self._zone_y = owner.rect.bottom

    def on_update(self, owner, event_bus=None, psys=None):
        if self.timer <= self.duration - self.WARN_FRAMES:
            target = getattr(owner, "_skill_target", None)
            if target and not target.dead:
                hb = self.get_hitbox(owner)
                if hb and hb.colliderect(target.rect):
                    target.vel.x *= self.SLOW_FACTOR
                    target.vel.y *= 0.88
            if psys and self.timer % 9 == 0:
                zx = getattr(self, "_zone_x", owner.rect.centerx)
                zy = getattr(self, "_zone_y", owner.rect.bottom)
                psys.spawn(zx + random.randint(-self.ZONE_W // 2, self.ZONE_W // 2),
                           zy - random.randint(10, self.ZONE_H),
                           random.choice([(55, 185, 165), (110, 205, 255), (220, 255, 255)]),
                           count=1, speed=1.8, life=18, r=3)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom)
        sx, sy = camera.world_to_screen(zx, zy)
        zw = int(self.ZONE_W * z)
        zh = int(self.ZONE_H * z)
        warn = self.timer > self.duration - self.WARN_FRAMES
        pulse = abs(math.sin(self.timer * 0.22))
        alpha = _clamp_alpha((80 if warn else 115) + pulse * 65)
        sf = pygame.Surface((zw, zh), pygame.SRCALPHA)
        fill = (255, 85, 80, 34) if warn else (*self.ZONE_COLOR, 42)
        pygame.draw.rect(sf, fill, (0, 0, zw, zh), border_radius=max(4, int(8 * z)))
        step = max(10, int(18 * z))
        for x in range(0, zw + 1, step):
            pygame.draw.line(sf, (*self.ZONE_GLOW, alpha // 2), (x, 0), (x, zh), 1)
        for y in range(0, zh + 1, step):
            pygame.draw.line(sf, (*self.ZONE_GLOW, alpha // 2), (0, y), (zw, y), 1)
        pygame.draw.rect(sf, (*self.ZONE_GLOW, alpha), (0, 0, zw, zh), max(1, int(2 * z)), border_radius=max(4, int(8 * z)))
        for i in range(4):
            y = int((i + 1) * zh / 5)
            pygame.draw.circle(sf, (220, 255, 255, alpha), (zw // 2 + int(math.sin(self.timer * 0.16 + i) * zw * 0.25), y), max(2, int(3 * z)))
        screen.blit(sf, (sx - zw // 2, sy - zh))

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.25
        target.vel.y *= 0.5
        super().on_hit(owner, target, event_bus, psys, fsys)


class TuringDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Turing Domain"
    DESCRIPTION = "Open Turing's universal machine domain."
    DOMAIN_BG_PATH = "assets/images/charactor/Turing/Turing_domain.jpeg"
    DOMAIN_PARTICLE_COLOR = (80, 235, 190)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 30
    CUTSCENE_ZOOM = 1.48
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Turing Domain", damage=0, duration=999999)


class UniversalTape(_DomainOnlyMixin, BitstreamPulse):
    DISPLAY_NAME = "Universal Tape"
    DESCRIPTION = "Domain skill - a larger binary pulse with finisher charge."
    PROJ_SPEED = 14.0
    PROJ_SIZE = 25
    PROJ_COLOR = (120, 245, 255)
    PROJ_GLOW = (45, 115, 255)
    COOLDOWN_SEC = 3.4

    def __init__(self):
        ProjectileSkill.__init__(self, "Universal Tape", damage=36, cooldown=204, duration=70)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.75
        self._spin = 0.0

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x += owner.facing * 10
        target.vel.y -= 4
        super().on_hit(owner, target, event_bus, psys, fsys)


class DecidabilityTrap(_DomainOnlyMixin, HaltingField):
    DISPLAY_NAME = "Decidability Trap"
    DESCRIPTION = "Domain skill - multi-hit computation field."
    WARN_FRAMES = 16
    ZONE_W = 235
    ZONE_H = 128
    ZONE_COLOR = (70, 120, 255)
    ZONE_GLOW = (170, 245, 255)
    COOLDOWN_SEC = 6.8
    SLOW_FACTOR = 0.35
    HIT_INTERVAL = 30

    def __init__(self):
        SummonZoneSkill.__init__(self, "Decidability Trap", damage=15, cooldown=408, duration=136)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.6
        self._hit_clock = 0

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        self._zone_x = owner.rect.centerx + owner.facing * 175
        self._zone_y = owner.rect.bottom
        self._hit_clock = 0

    def on_update(self, owner, event_bus=None, psys=None):
        if self.timer <= self.duration - self.WARN_FRAMES:
            self._hit_clock += 1
            if self._hit_clock >= self.HIT_INTERVAL:
                self._hit_clock = 0
                self.has_hit = False
        super().on_update(owner, event_bus, psys)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.15
        target.vel.y -= 2
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW, count=14, speed=4, life=20, r=4)
        super().on_hit(owner, target, event_bus, psys, fsys)


class Turing(Player):
    WEIGHT = 106
    KB_GROWTH = 78
    BASE_KB = 34
    WALK_SPEED = 6.0
    JUMP_POWER = -14.8
    MAX_JUMPS = 2
    ATTACK_DMG = 14
    ATK_FRAMES = 23
    ATK_CD = 38
    HIT_START = 5
    HIT_END = 17

    BODY_COLOR = (55, 185, 165)
    TRIM_COLOR = (20, 95, 120)
    GLOW_COLOR = (120, 220, 255)
    DARK_COLOR = (10, 45, 65)
    DISPLAY_NAME = "Turing"
    DESCRIPTION = "Computation zoner.\nControls movement with bit pulses and fields."
    PREVIEW_COLOR = (55, 185, 165)
    SKILL_NAME = "Bitstream Pulse"

    SPRITE_PATH = "assets/images/charactor/Turing/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Turing/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Turing/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Turing/attack.png"
    SPRITE_SKILL = "assets/images/charactor/Turing/skill.png"

    SPRITE_SCALE = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Bitstream Pulse", "ProjectileSkill", 22, 28, 4.0),
        "cc": ("Halting Field", "SummonZoneSkill", 18, 34, 8.0),
        "enhance": ("Turing Domain", "DomainUltimateSkill", 0, 0, 0.0),
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
        self.skills["skill_Q"] = BitstreamPulse()
        self.skills["skill_E"] = HaltingField()
        self.skills["skill_R"] = TuringDomain()
        self.skills["skill_Q_domain"] = UniversalTape()
        self.skills["skill_E_domain"] = DecidabilityTrap()

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
        return "Turing"
