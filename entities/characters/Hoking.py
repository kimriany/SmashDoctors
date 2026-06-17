"""
Hoking — 블랙홀과 시간 지연으로 공간을 잠그는 중거리 캐릭터.

일반 스킬:
  Q / ;  Hawking Shard      — ProjectileSkill, 아티팩트 발사체
  E / '  Time Dilation      — SummonZoneSkill, 시간 지연 구역
  R / /  Hoking Domain      — hoking_domain.png 영역 전개

영역 전개 중 강화 스킬:
  Q / ;  Singularity Shard  — 더 빠르고 강한 발사체
  E / '  Entropy Horizon    — 넓은 다단 블랙홀 구역
"""
from entities.player import Player
from systems.skill import Skill, BeamSkill, ProjectileSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


ARTIFACT = "assets/images/charactor/hoking/hoking_artifact_skill.png"
DOMAIN_BG = "assets/images/charactor/hoking/hoking_domain.png"
VOID_COLORS = (
    (5, 8, 24),
    (12, 22, 58),
    (28, 72, 150),
    (45, 145, 255),
    (190, 230, 255),
)


def _alpha(v):
    return max(0, min(255, int(v)))


class _DomainOnlyMixin:
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


class HawkingShard(_NormalOnlyMixin, ProjectileSkill):
    DISPLAY_NAME = "Hawking Shard"
    DESCRIPTION = "Throw a dense gravity artifact.\nFast projectile with a blue radiation trail."
    ARTIFACT_PATH = ARTIFACT
    ICON_PATH = ARTIFACT
    PROJ_SPEED = 10.5
    PROJ_SIZE = 18
    PROJ_COLOR = (120, 210, 255)
    PROJ_GLOW = (210, 245, 255)
    COOLDOWN_SEC = 4.2

    def __init__(self):
        super().__init__("Hawking Shard", damage=21, cooldown=252, duration=78)
        self.charge_value = 0.9

    def on_start(self, owner, event_bus=None, psys=None):
        self._px = float(owner.rect.centerx + owner.facing * 30)
        self._py = float(owner.rect.centery - 8)
        self._vx = self.PROJ_SPEED * owner.facing
        self._vy = -1.0
        self._alive = True
        if psys:
            psys.spawn(self._px, self._py, (8, 12, 36),
                       count=16, speed=4.2, gravity=-0.03, life=30, r=6, glow=True)
            psys.spawn(self._px, self._py, (70, 165, 255),
                       count=10, speed=5.4, gravity=-0.05, life=24, r=4, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive:
            return
        self._px += self._vx
        self._py += self._vy + math.sin(self.timer * 0.22) * 0.4
        self._vy *= 0.985

        if psys and self.timer % 3 == 0:
            psys.spawn(self._px - owner.facing * 12, self._py,
                       random.choice(VOID_COLORS),
                       count=3, speed=2.4, gravity=-0.04, life=20, r=3, glow=True)
        if psys and self.timer % 7 == 0:
            psys.spawn(self._px - owner.facing * 20, self._py,
                       (3, 5, 18), count=2, speed=1.6,
                       gravity=0.0, life=26, r=5, glow=True)

        if abs(self._px - owner.rect.centerx) > 820:
            self._alive = False

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._alive = False
        target.vel.x += owner.facing * 7
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, (45, 35, 80),
                       count=18, speed=5, gravity=0.02, life=30, r=5)
            psys.spawn(target.rect.centerx, target.rect.centery, (80, 170, 255),
                       count=24, speed=8, gravity=-0.05, life=34, r=5, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery, (235, 250, 255),
                       count=8, speed=4, gravity=-0.08, life=18, r=3, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active or not getattr(self, "_alive", False):
            return

        sx, sy = camera.world_to_screen(self._px, self._py)
        r = max(5, int(self.PROJ_SIZE * z))

        for i in range(3):
            trail_r = int(r * (1.9 - i * 0.35))
            alpha = 50 - i * 11
            surf = pygame.Surface((trail_r * 2, trail_r * 2), pygame.SRCALPHA)
            col = (30, 115, 255) if i < 2 else (5, 8, 24)
            pygame.draw.circle(surf, (*col, alpha), (trail_r, trail_r), trail_r)
            screen.blit(surf, (sx - owner.facing * (i + 1) * r - trail_r, sy - trail_r),
                        special_flags=pygame.BLEND_RGBA_ADD)

        rim_r = int(r * 1.45)
        rim = pygame.Surface((rim_r * 2 + 4, rim_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(rim, (210, 240, 255, 105), (rim_r + 2, rim_r + 2), rim_r, 2)
        pygame.draw.circle(rim, (2, 4, 14, 120), (rim_r + 2, rim_r + 2), max(1, int(rim_r * 0.55)))
        screen.blit(rim, (sx - rim_r - 2, sy - rim_r - 2), special_flags=pygame.BLEND_RGBA_ADD)

        super().draw_front(owner, screen, camera, dr, bob, z)


class TimeDilation(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Time Dilation"
    DESCRIPTION = "Open a small time-warp field.\nEnemies inside are slowed."
    ICON_PATH = ARTIFACT
    WARN_FRAMES = 28
    ZONE_W = 125
    ZONE_H = 96
    ZONE_COLOR = (70, 150, 255)
    ZONE_GLOW = (190, 230, 255)
    COOLDOWN_SEC = 8.0

    def __init__(self):
        super().__init__("Time Dilation", damage=20, cooldown=480, duration=104)
        self.charge_value = 1.2

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx - owner.rect.centerx) < 300:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 185
            self._zone_y = owner.rect.bottom

    def on_update(self, owner, event_bus=None, psys=None):
        active_phase = self.timer <= self.duration - self.WARN_FRAMES
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2

        if active_phase:
            target = getattr(owner, "_skill_target", None)
            if target and not target.dead:
                field = self.get_hitbox(owner)
                if field and field.colliderect(target.rect):
                    target.vel.x *= 0.82
                    target.vel.y *= 0.88

        if psys and self.timer % 5 == 0:
            for i in range(4):
                ang = self.timer * 0.13 + i * math.pi * 0.5
                rad = random.randint(25, self.ZONE_W // 2)
                psys.spawn(zx + math.cos(ang) * rad, zy + math.sin(ang) * rad,
                           random.choice([(235, 250, 255), (210, 235, 255), (8, 10, 28)]),
                           count=1, speed=0.9, gravity=-0.02, life=18, r=2, glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.55
        target.vel.y *= 0.75
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, (8, 10, 32),
                       count=20, speed=5, gravity=0.0, life=34, r=6, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW,
                       count=18, speed=7, gravity=-0.04, life=28, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return

        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
        sx, sy = camera.world_to_screen(zx, zy)

        warn = self.timer > self.duration - self.WARN_FRAMES
        t = self.timer / max(1, self.duration)
        base_r = int((self.ZONE_W // 2) * z)
        pulse = int(math.sin(pygame.time.get_ticks() * 0.01) * 5 * z)
        alpha = 72 if warn else max(34, int(82 * t))

        # Before domain: translucent black core with stacked white event-horizon rings.
        for mult, col, a in (
            (1.28, (255, 255, 255), alpha),
            (0.98, (235, 245, 255), max(28, alpha - 12)),
            (0.72, (255, 255, 255), max(22, alpha - 20)),
            (0.42, (0, 0, 0), 74),
        ):
            rr = max(1, int(base_r * mult + pulse))
            surf = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*col, a), (rr, rr), rr)
            screen.blit(surf, (sx - rr, sy - rr))

        for i, (mult, width, a) in enumerate((
            (1.34, 2, 170 if warn else 125),
            (1.12, 2, 135 if warn else 105),
            (0.9, 2, 120 if warn else 92),
            (0.68, 2, 110 if warn else 82),
            (0.48, 3, 150 if warn else 110),
        )):
            ring_r = max(1, int(base_r * mult + (pulse if i % 2 == 0 else -pulse * 0.4)))
            ring = pygame.Surface((ring_r * 2 + 10, ring_r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(ring, (245, 250, 255, a), (ring_r + 5, ring_r + 5),
                               ring_r, max(1, int(width * z)))
            screen.blit(ring, (sx - ring_r - 5, sy - ring_r - 5))


class HokingDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Hoking Domain"
    DESCRIPTION = "Open a black-hole domain.\nRadiation skills become stronger."
    DOMAIN_BG_PATH = DOMAIN_BG
    DOMAIN_PARTICLE_COLOR = (120, 210, 255)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 34
    CUTSCENE_ZOOM = 1.5
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Hoking Domain", damage=0, duration=999999)


class SingularityShard(_DomainOnlyMixin, HawkingShard):
    DISPLAY_NAME = "Singularity Shard"
    DESCRIPTION = "Domain skill — compressed black-hole projectile.\nFaster, stronger, brighter."
    PROJ_SPEED = 14.0
    PROJ_SIZE = 24
    COOLDOWN_SEC = 3.0

    def __init__(self):
        ProjectileSkill.__init__(self, "Singularity Shard", damage=38, cooldown=180, duration=74)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.9

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        self._vy = -0.4
        if psys:
            for _ in range(32):
                psys.spawn(self._px, self._py,
                           random.choice([(110, 210, 255), (255, 255, 255), (70, 60, 150)]),
                           count=1, speed=random.uniform(3, 9),
                           gravity=random.uniform(-0.08, 0.04),
                           life=random.randint(18, 34), r=random.randint(3, 7), glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.y -= 6
        super().on_hit(owner, target, event_bus, psys, fsys)


class EntropyHorizon(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Entropy Horizon"
    DESCRIPTION = "Domain skill — translucent event horizon.\nEnemies inside are heavily slowed."
    ICON_PATH = ARTIFACT
    WARN_FRAMES = 0
    ZONE_W = 220
    ZONE_H = 180
    ZONE_COLOR = (40, 80, 180)
    ZONE_GLOW = (170, 230, 255)
    COOLDOWN_SEC = 7.0
    MULTI_HIT_INTERVAL = 24

    def __init__(self):
        super().__init__("Entropy Horizon", damage=14, cooldown=420, duration=150)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.7
        self._hit_timer = 0

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx - owner.rect.centerx) < 360:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        self._hit_timer = 0
        if psys:
            zx = getattr(self, "_zone_x", owner.rect.centerx)
            zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
            psys.spawn(zx, zy, self.ZONE_GLOW, count=34, speed=8, gravity=-0.08, life=38, r=6, glow=True)
            psys.spawn(zx, zy, (3, 4, 16), count=30, speed=4.5, gravity=0.0, life=48, r=8, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2

        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            field = self.get_hitbox(owner)
            if field and field.colliderect(target.rect):
                target.vel.x *= 0.72
                target.vel.y *= 0.82

        self._hit_timer += 1
        if self._hit_timer >= self.MULTI_HIT_INTERVAL:
            self._hit_timer = 0
            self.has_hit = False

        if psys and self.timer % 3 == 0:
            for i in range(4):
                ang = self.timer * 0.19 + i * math.pi * 2 / 3
                rad = random.randint(34, self.ZONE_W // 2)
                psys.spawn(zx + math.cos(ang) * rad, zy + math.sin(ang) * rad,
                           random.choice([(255, 255, 255), (75, 165, 255), (10, 16, 45)]),
                           count=1, speed=1.6, gravity=-0.04, life=18, r=random.randint(2, 5), glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.55
        target.vel.y *= 0.7
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW,
                       count=24, speed=7, gravity=-0.04, life=28, r=5, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
        return pygame.Rect(zx - self.ZONE_W // 2, zy - self.ZONE_H // 2,
                           self.ZONE_W, self.ZONE_H)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return

        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
        sx, sy = camera.world_to_screen(zx, zy)
        base_r = int(self.ZONE_W * 0.48 * z)
        pulse = int(math.sin(pygame.time.get_ticks() * 0.011) * 6 * z)

        for mult, col, a in (
            (1.34, (255, 255, 255), 42),
            (1.08, (50, 150, 255), 50),
            (0.76, (8, 14, 46), 88),
            (0.38, (0, 0, 0), 96),
        ):
            rr = max(1, int(base_r * mult + pulse))
            surf = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*col, a), (rr, rr), rr)
            screen.blit(surf, (sx - rr, sy - rr))

        # In domain: alternating white and blue translucent horizon bands.
        ring_specs = (
            (1.42, (245, 250, 255), 3, 150),
            (1.22, (50, 160, 255), 3, 130),
            (1.02, (245, 250, 255), 2, 120),
            (0.82, (50, 160, 255), 2, 112),
            (0.62, (245, 250, 255), 2, 108),
            (0.44, (50, 160, 255), 2, 96),
        )
        for i, (mult, col, width, alpha) in enumerate(ring_specs):
            rr = max(1, int(base_r * mult + (pulse if i % 2 == 0 else -pulse * 0.45)))
            ring = pygame.Surface((rr * 2 + 10, rr * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*col, alpha),
                               (rr + 5, rr + 5), rr, max(1, int(width * z)))
            screen.blit(ring, (sx - rr - 5, sy - rr - 5))


class HawkingRadiation(_NormalOnlyMixin, BeamSkill):
    DISPLAY_NAME = "Hawking Radiation"
    DESCRIPTION = "Emit a thin radiation jet. Fast, clean, and precise."
    BEAM_LENGTH = 310
    BEAM_WIDTH = 22
    BEAM_COLOR = (120, 225, 255)
    BEAM_GLOW = (245, 255, 255)
    COOLDOWN_SEC = 4.0

    def __init__(self):
        super().__init__("Hawking Radiation", damage=23, cooldown=240, duration=20)
        self.charge_value = 1.0
        self._cast_facing = 1

    def on_start(self, owner, event_bus=None, psys=None):
        self._cast_facing = owner.facing
        if psys:
            for _ in range(18):
                psys.spawn(owner.rect.centerx + self._cast_facing * random.randint(20, 80),
                           owner.rect.centery + random.randint(-18, 18),
                           random.choice([(120,225,255), (245,255,255), (45,145,255)]),
                           count=1, speed=random.uniform(3, 8), gravity=-0.06,
                           life=random.randint(12, 24), r=random.randint(2, 5), glow=True)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        w = self.BEAM_LENGTH
        h = self.BEAM_WIDTH + 18
        facing = getattr(self, "_cast_facing", owner.facing)
        ox = owner.rect.right - 6 if facing == 1 else owner.rect.left - w + 6
        return pygame.Rect(ox, owner.rect.centery - h//2, w, h)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        facing = getattr(self, "_cast_facing", owner.facing)
        target.vel.x += facing * 9
        target.vel.y -= 2
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, (245,255,255),
                       count=18, speed=7, gravity=-0.05, life=22, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        facing = getattr(self, "_cast_facing", owner.facing)
        t = self.timer / max(1, self.duration)
        alpha = max(30, int(230 * t))
        length = int(self.BEAM_LENGTH * z)
        sx = dr.right - int(6*z) if facing == 1 else dr.left - length + int(6*z)
        sy = dr.centery + bob
        for i in range(4):
            width = max(1, int((self.BEAM_WIDTH - i*4) * z * t))
            surf = pygame.Surface((length, width + 12), pygame.SRCALPHA)
            pygame.draw.rect(surf, (120,225,255,_alpha(alpha - i*35)),
                             (0, 6, length, width), border_radius=max(1,int(3*z)))
            pygame.draw.rect(surf, (245,255,255,_alpha((alpha - i*35)*0.55)),
                             (0, 6+width//2, length, max(1,int(2*z))))
            screen.blit(surf, (sx, sy - width//2 - 6 + int(math.sin(i+pygame.time.get_ticks()*0.02)*4*z)))


class TimeSlip(_NormalOnlyMixin, Skill):
    DISPLAY_NAME = "Time Slip"
    DESCRIPTION = "Slip through time and leave a delayed radiation burst."
    COOLDOWN_SEC = 8.0
    SLIP_DISTANCE = 145
    BURST_FRAME = 18

    def __init__(self):
        super().__init__("Time Slip", damage=28, cooldown=480, duration=46)
        self.charge_value = 1.3
        self._origin = (0, 0)
        self._burst_done = False
        self._cast_facing = 1

    def on_start(self, owner, event_bus=None, psys=None):
        self._cast_facing = owner.facing
        self._origin = (owner.rect.centerx, owner.rect.centery)
        self._burst_done = False
        owner.rect.x += self._cast_facing * self.SLIP_DISTANCE
        owner.invincible = max(owner.invincible, 20)
        if psys:
            psys.spawn(self._origin[0], self._origin[1], (120,225,255),
                       count=24, speed=7, gravity=-0.05, life=26, r=5, glow=True)
            psys.spawn(owner.rect.centerx, owner.rect.centery, (245,255,255),
                       count=18, speed=5, gravity=-0.04, life=22, r=4, glow=True)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        elapsed = self.duration - self.timer
        if elapsed < self.BURST_FRAME or elapsed > self.BURST_FRAME + 8:
            return None
        r = 76
        return pygame.Rect(self._origin[0]-r, self._origin[1]-r, r*2, r*2)

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        if elapsed == self.BURST_FRAME:
            self.has_hit = False
            self._burst_done = True
            if psys:
                psys.spawn(self._origin[0], self._origin[1], (245,255,255),
                           count=34, speed=9, gravity=-0.04, life=30, r=6, glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x += self._cast_facing * 10
        target.vel.y -= 7
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        ox, oy = camera.world_to_screen(*self._origin)
        t = self.timer / max(1, self.duration)
        rr = max(8, int((50 + 22 * math.sin(pygame.time.get_ticks()*0.015)) * z))
        surf = pygame.Surface((rr*2+8, rr*2+8), pygame.SRCALPHA)
        pygame.draw.circle(surf, (120,225,255,_alpha(90*t)), (rr+4, rr+4), rr)
        pygame.draw.circle(surf, (245,255,255,_alpha(160*t)), (rr+4, rr+4), rr, max(2,int(3*z)))
        screen.blit(surf, (ox-rr-4, oy-rr-4))


class GammaRayBurst(_DomainOnlyMixin, HawkingRadiation):
    DISPLAY_NAME = "Gamma-Ray Burst"
    DESCRIPTION = "Domain — three stacked radiation jets tear through spacetime."
    BEAM_LENGTH = 430
    BEAM_WIDTH = 34
    COOLDOWN_SEC = 4.5

    def __init__(self):
        BeamSkill.__init__(self, "Gamma-Ray Burst", damage=40, cooldown=270, duration=28)
        self.charge_value = 0.0
        self.finisher_charge_value = 2.0
        self._cast_facing = 1

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        facing = getattr(self, "_cast_facing", owner.facing)
        target.vel.x = facing * 18
        target.vel.y -= 8
        super().on_hit(owner, target, event_bus, psys, fsys)


class InformationParadox(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Information Paradox"
    DESCRIPTION = "Domain — mark a zone that replays damage as delayed radiation."
    WARN_FRAMES = 12
    ZONE_W = 300
    ZONE_H = 220
    ZONE_COLOR = (70, 170, 255)
    ZONE_GLOW = (245, 255, 255)
    COOLDOWN_SEC = 10.5
    TICK_INTERVAL = 26

    def __init__(self):
        super().__init__("Information Paradox", damage=15, cooldown=630, duration=170)
        self.charge_value = 0.0
        self.finisher_charge_value = 2.6
        self._tick_timer = 0
        self._phase = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.centery
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 190
            self._zone_y = owner.rect.centery
        self._tick_timer = 0
        self._phase = random.uniform(0, math.pi*2)
        self.has_hit = False
        if psys:
            psys.spawn(self._zone_x, self._zone_y, (245,255,255),
                       count=36, speed=8, gravity=-0.05, life=38, r=5, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        self._phase += 0.08
        target = getattr(owner, "_skill_target", None)
        zone = self.get_hitbox(owner)
        if target and not target.dead and zone and zone.colliderect(target.rect):
            target.vel.x *= 0.78
            target.vel.y *= 0.86
            self._tick_timer += 1
            if self._tick_timer >= self.TICK_INTERVAL:
                self._tick_timer = 0
                self.has_hit = False
        if psys and self.timer % 4 == 0:
            ang = self._phase + random.uniform(0, math.pi*2)
            rad = random.uniform(30, self.ZONE_W * 0.45)
            psys.spawn(self._zone_x + math.cos(ang)*rad,
                       self._zone_y + math.sin(ang)*rad,
                       random.choice([(120,225,255), (245,255,255), (30,80,180)]),
                       count=1, speed=1.2, gravity=-0.03, life=18, r=random.randint(2, 5), glow=True)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        elapsed = self.duration - self.timer
        if elapsed < self.WARN_FRAMES:
            return None
        return pygame.Rect(int(self._zone_x)-self.ZONE_W//2,
                           int(self._zone_y)-self.ZONE_H//2,
                           self.ZONE_W, self.ZONE_H)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.55
        target.vel.y -= 4
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, (245,255,255),
                       count=22, speed=7, gravity=-0.04, life=24, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        sx, sy = camera.world_to_screen(int(self._zone_x), int(self._zone_y))
        elapsed = self.duration - self.timer
        warn = elapsed < self.WARN_FRAMES
        alpha = _alpha(90 + 90 * abs(math.sin(elapsed*0.22))) if warn else _alpha(120*self.timer/self.duration)
        zw, zh = int(self.ZONE_W*z), int(self.ZONE_H*z)
        surf = pygame.Surface((zw+12, zh+12), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (70,170,255,_alpha(alpha*0.22)), (6,6,zw,zh))
        pygame.draw.ellipse(surf, (245,255,255,alpha), (6,6,zw,zh), max(2,int(3*z)))
        for i in range(7):
            x = 6 + int((i+1) * zw / 8)
            pygame.draw.line(surf, (245,255,255,_alpha(alpha*0.45)), (x, 12), (x, zh), max(1,int(1*z)))
        screen.blit(surf, (sx-zw//2-6, sy-zh//2-6))


class Hoking(Player):
    WEIGHT = 98
    KB_GROWTH = 80
    BASE_KB = 31
    WALK_SPEED = 5.9
    JUMP_POWER = -15.0
    MAX_JUMPS = 2
    ATTACK_DMG = 13
    ATK_FRAMES = 21
    ATK_CD = 34
    HIT_START = 4
    HIT_END = 16

    BODY_COLOR = (60, 120, 210)
    TRIM_COLOR = (22, 44, 110)
    GLOW_COLOR = (130, 220, 255)
    DARK_COLOR = (10, 18, 46)
    DISPLAY_NAME = "Hoking"
    DESCRIPTION = (
        "Black-hole zoner with radiant projectiles.\n"
        "Domain turns gravity into a weapon."
    )
    PREVIEW_COLOR = (60, 120, 210)
    SKILL_NAME = "Hawking Shard"

    SPRITE_PATH = "assets/images/charactor/hoking/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/hoking/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/hoking/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/hoking/attack.png"
    SPRITE_SKILL = "assets/images/charactor/hoking/skill.png"

    SPRITE_SCALE = 1.25
    SPRITE_SCALE_X = 1.35
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Hawking Radiation", "BeamSkill", 23, 26, 4.0),
        "cc": ("Time Slip", "Skill", 28, 38, 8.0),
        "enhance": ("Hoking Domain", "DomainUltimateSkill", 0, 0, 0.0),
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
        self.skills["skill_Q"] = HawkingRadiation()
        self.skills["skill_E"] = TimeSlip()
        self.skills["skill_R"] = HokingDomain()
        self.skills["skill_Q_domain"] = GammaRayBurst()
        self.skills["skill_E_domain"] = InformationParadox()

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
        return "Hoking"
