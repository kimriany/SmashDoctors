"""
Schrodinger — 원자 궤도와 파동 간섭으로 공간을 제어하는 콤보 캐릭터.

일반 스킬:
  Q / ;  Atomic Wave       — ProjectileSkill, 사인파로 이동하는 원자 발사체
  E / '  Interference Well — SummonZoneSkill, 파동 간섭 필드
  R / /  Superposition     — schrodinger_domain.png 영역 전개

영역 전개 중 강화 스킬:
  Q / ;  Quantum Packet    — 더 빠르고 강한 파동 발사체
  E / '  Probability Cloud — 넓은 다단 파동 필드
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


DOMAIN_BG = "assets/images/charactor/Schrödinger/schrodinger_domain.png"
ATOM_COLORS = (
    (90, 210, 255),
    (160, 120, 255),
    (235, 245, 255),
    (80, 255, 210),
)


def _alpha(value):
    return max(0, min(255, int(value)))


class _DomainOnlyMixin:
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


class AtomicWave(_NormalOnlyMixin, ProjectileSkill):
    DISPLAY_NAME = "Atomic Wave"
    DESCRIPTION = "Fire an atom packet with a wave trail."
    PROJ_SPEED = 10.0
    PROJ_SIZE = 17
    PROJ_COLOR = (95, 220, 255)
    PROJ_GLOW = (210, 245, 255)
    COOLDOWN_SEC = 3.5

    def __init__(self):
        super().__init__("Atomic Wave", damage=18, cooldown=210, duration=84)
        self.charge_value = 0.9

    def on_start(self, owner, event_bus=None, psys=None):
        self._origin_y = float(owner.rect.centery - 6)
        self._px = float(owner.rect.centerx + owner.facing * 30)
        self._py = self._origin_y
        self._vx = self.PROJ_SPEED * owner.facing
        self._phase = random.uniform(0, math.pi * 2)
        self._alive = True
        if psys:
            psys.spawn(self._px, self._py, (90, 210, 255), count=14,
                       speed=4.5, gravity=-0.04, life=24, r=4, glow=True)
            psys.spawn(self._px, self._py, (170, 120, 255), count=8,
                       speed=3.2, gravity=-0.02, life=20, r=3, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive:
            return
        elapsed = self.duration - self.timer
        self._px += self._vx
        self._py = self._origin_y

        if psys and self.timer % 3 == 0:
            wave_y = self._py + math.sin(elapsed * 0.34 + self._phase) * 22
            psys.spawn(self._px - owner.facing * 14, wave_y,
                       random.choice(ATOM_COLORS), count=2, speed=2.0,
                       gravity=-0.03, life=18, r=3, glow=True)
        if abs(self._px - owner.rect.centerx) > 760:
            self._alive = False

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._alive = False
        target.vel.y -= 4
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, (90, 220, 255),
                       count=24, speed=7, gravity=-0.06, life=30, r=5, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery, (190, 130, 255),
                       count=16, speed=5, gravity=-0.02, life=24, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active or not getattr(self, "_alive", False):
            return

        sx, sy = camera.world_to_screen(self._px, self._py)
        r = max(5, int(self.PROJ_SIZE * z))
        elapsed = self.duration - self.timer

        # 파동 궤적
        points = []
        mirror_points = []
        for i in range(18):
            x = sx - owner.facing * i * 9 * z
            y = sy + math.sin(elapsed * 0.34 - i * 0.55 + self._phase) * 11 * z
            y2 = sy - math.sin(elapsed * 0.34 - i * 0.55 + self._phase) * 11 * z
            points.append((x, y))
            mirror_points.append((x, y2))
        if len(points) > 1:
            bounds = pygame.Rect(0, 0, screen.get_width(), screen.get_height())
            wave = pygame.Surface(bounds.size, pygame.SRCALPHA)
            pygame.draw.lines(wave, (95, 220, 255, 150), False, points, max(1, int(2 * z)))
            pygame.draw.lines(wave, (180, 120, 255, 105), False, mirror_points, max(1, int(2 * z)))
            screen.blit(wave, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # 원자 궤도 링
        ring = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
        cx = cy = r * 5 // 2
        pygame.draw.circle(ring, (20, 28, 70, 130), (cx, cy), int(r * 1.1))
        pygame.draw.circle(ring, (230, 250, 255, 230), (cx, cy), max(2, r // 3))
        for i, angle in enumerate((0, math.pi / 3, -math.pi / 3)):
            rect = pygame.Rect(cx - int(r * 1.8), cy - int(r * 0.58), int(r * 3.6), int(r * 1.16))
            orbit = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
            pygame.draw.ellipse(orbit, (*ATOM_COLORS[i], 135), rect, max(1, int(2 * z)))
            rotated = pygame.transform.rotate(orbit, math.degrees(angle) + elapsed * 7)
            screen.blit(rotated, (sx - rotated.get_width() // 2, sy - rotated.get_height() // 2),
                        special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(ring, (sx - cx, sy - cy), special_flags=pygame.BLEND_RGBA_ADD)


class InterferenceWell(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Interference Well"
    DESCRIPTION = "Create overlapping wave rings that slow enemies."
    WARN_FRAMES = 24
    ZONE_W = 150
    ZONE_H = 110
    ZONE_COLOR = (115, 170, 255)
    ZONE_GLOW = (220, 245, 255)
    COOLDOWN_SEC = 7.0

    def __init__(self):
        super().__init__("Interference Well", damage=17, cooldown=420, duration=108)
        self.charge_value = 1.15

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx - owner.rect.centerx) < 330:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 190
            self._zone_y = owner.rect.bottom
        self._phase = random.uniform(0, math.pi * 2)

    def on_update(self, owner, event_bus=None, psys=None):
        active_phase = self.timer <= self.duration - self.WARN_FRAMES
        if active_phase:
            target = getattr(owner, "_skill_target", None)
            if target and not target.dead:
                field = self.get_hitbox(owner)
                if field and field.colliderect(target.rect):
                    target.vel.x *= 0.84
                    target.vel.y *= 0.9

        if psys and self.timer % 5 == 0:
            zx = getattr(self, "_zone_x", owner.rect.centerx)
            zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
            for i in range(4):
                ang = self.timer * 0.16 + i * math.pi * 0.5
                psys.spawn(zx + math.cos(ang) * random.randint(18, self.ZONE_W // 2),
                           zy + math.sin(ang) * random.randint(12, self.ZONE_H // 2),
                           random.choice(ATOM_COLORS), count=1, speed=1.2,
                           gravity=-0.03, life=18, r=3, glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.5
        target.vel.y -= 3
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW,
                       count=24, speed=6, gravity=-0.05, life=28, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
        sx, sy = camera.world_to_screen(zx, zy)
        warn = self.timer > self.duration - self.WARN_FRAMES
        t = self.timer / max(1, self.duration)
        base_w = int(self.ZONE_W * z)
        base_h = int(self.ZONE_H * z)
        pulse = math.sin(pygame.time.get_ticks() * 0.01 + self._phase)
        alpha = 72 if warn else int(90 * t)

        surf = pygame.Surface((base_w + 60, base_h + 60), pygame.SRCALPHA)
        cx, cy = surf.get_width() // 2, surf.get_height() // 2
        pygame.draw.ellipse(surf, (25, 22, 70, 42),
                            (30, 30, base_w, base_h))
        for i in range(5):
            shrink = i * 13 * z + pulse * 3 * z
            rect = pygame.Rect(
                int(30 + shrink), int(30 + shrink * 0.65),
                max(4, int(base_w - shrink * 2)), max(4, int(base_h - shrink * 1.3)),
            )
            col = (220, 245, 255) if i % 2 == 0 else (125, 170, 255)
            pygame.draw.ellipse(surf, (*col, _alpha(alpha - i * 8)), rect, max(1, int(2 * z)))

        # 이중 슬릿 간섭선 느낌
        for xoff in (-base_w * 0.18, base_w * 0.18):
            pygame.draw.circle(surf, (235, 250, 255, 135),
                               (int(cx + xoff), cy), max(2, int(4 * z)))
        screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))


class SchrodingerDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Superposition Domain"
    DESCRIPTION = "Open Schrodinger's quantum domain."
    DOMAIN_BG_PATH = DOMAIN_BG
    DOMAIN_PARTICLE_COLOR = (170, 120, 255)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 32
    CUTSCENE_ZOOM = 1.46
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Superposition Domain", damage=0, duration=999999)


class QuantumPacket(_DomainOnlyMixin, AtomicWave):
    DISPLAY_NAME = "Quantum Packet"
    DESCRIPTION = "Domain skill — faster atom wave with stronger collapse."
    PROJ_SPEED = 14.0
    PROJ_SIZE = 22
    COOLDOWN_SEC = 2.6

    def __init__(self):
        ProjectileSkill.__init__(self, "Quantum Packet", damage=32, cooldown=156, duration=76)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.7

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        if psys:
            for _ in range(24):
                psys.spawn(self._px, self._py, random.choice(ATOM_COLORS),
                           count=1, speed=random.uniform(3, 8), gravity=-0.05,
                           life=random.randint(18, 32), r=random.randint(3, 6), glow=True)


class ProbabilityCloud(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Probability Cloud"
    DESCRIPTION = "Domain skill — large quantum cloud with repeated wave hits."
    WARN_FRAMES = 0
    ZONE_W = 230
    ZONE_H = 170
    ZONE_COLOR = (125, 120, 255)
    ZONE_GLOW = (225, 245, 255)
    COOLDOWN_SEC = 6.5
    MULTI_HIT_INTERVAL = 26

    def __init__(self):
        super().__init__("Probability Cloud", damage=13, cooldown=390, duration=144)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.6
        self._hit_timer = 0

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx - owner.rect.centerx) < 390:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        self._hit_timer = 0
        if psys:
            zx = getattr(self, "_zone_x", owner.rect.centerx)
            zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
            psys.spawn(zx, zy, (150, 120, 255), count=32, speed=7,
                       gravity=-0.06, life=38, r=6, glow=True)
            psys.spawn(zx, zy, (90, 220, 255), count=20, speed=5,
                       gravity=-0.04, life=30, r=4, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom) - self.ZONE_H // 2
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            field = self.get_hitbox(owner)
            if field and field.colliderect(target.rect):
                target.vel.x *= 0.78
                target.vel.y *= 0.86

        self._hit_timer += 1
        if self._hit_timer >= self.MULTI_HIT_INTERVAL:
            self._hit_timer = 0
            self.has_hit = False

        if psys and self.timer % 4 == 0:
            for i in range(5):
                ang = self.timer * 0.17 + i * math.pi * 2 / 5
                rad = random.randint(25, self.ZONE_W // 2)
                psys.spawn(zx + math.cos(ang) * rad,
                           zy + math.sin(ang * 1.3) * random.randint(18, self.ZONE_H // 2),
                           random.choice(ATOM_COLORS), count=1, speed=1.8,
                           gravity=-0.04, life=20, r=random.randint(2, 5), glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.65
        target.vel.y -= 4
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW,
                       count=22, speed=6, gravity=-0.05, life=24, r=4, glow=True)
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
        bw = int(self.ZONE_W * z)
        bh = int(self.ZONE_H * z)
        pulse = math.sin(pygame.time.get_ticks() * 0.012)

        surf = pygame.Surface((bw + 90, bh + 90), pygame.SRCALPHA)
        cx, cy = surf.get_width() // 2, surf.get_height() // 2
        pygame.draw.ellipse(surf, (38, 20, 80, 68), (45, 45, bw, bh))
        for i in range(7):
            shrink = (i * 12 + pulse * 4) * z
            rect = pygame.Rect(
                int(45 + shrink), int(45 + shrink * 0.62),
                max(4, int(bw - shrink * 2)), max(4, int(bh - shrink * 1.25)),
            )
            col = ATOM_COLORS[i % len(ATOM_COLORS)]
            pygame.draw.ellipse(surf, (*col, _alpha(112 - i * 8)), rect, max(1, int(2 * z)))

        # 원자 궤도 3겹
        for angle, col in ((0, (235, 245, 255)), (55, (120, 220, 255)), (-55, (180, 120, 255))):
            orbit = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            rect = pygame.Rect(cx - bw // 2, cy - bh // 4, bw, max(8, bh // 2))
            pygame.draw.ellipse(orbit, (*col, 92), rect, max(1, int(2 * z)))
            rotated = pygame.transform.rotate(orbit, angle + pygame.time.get_ticks() * 0.02)
            surf.blit(rotated, (cx - rotated.get_width() // 2, cy - rotated.get_height() // 2),
                      special_flags=pygame.BLEND_RGBA_ADD)

        screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))


class Schrödinger(Player):
    WEIGHT = 96
    KB_GROWTH = 78
    BASE_KB = 30
    WALK_SPEED = 6.2
    JUMP_POWER = -15.0
    MAX_JUMPS = 2
    ATTACK_DMG = 9
    ATK_FRAMES = 16
    ATK_CD = 26
    HIT_START = 3
    HIT_END = 13

    BODY_COLOR = (155, 60, 220)
    TRIM_COLOR = (90, 20, 140)
    GLOW_COLOR = (210, 130, 255)
    DARK_COLOR = (60, 10, 100)
    DISPLAY_NAME = "Schrödinger"
    DESCRIPTION = (
        "Atom and wave combo fighter.\n"
        "Domain strengthens probability skills."
    )
    PREVIEW_COLOR = (155, 60, 220)
    SKILL_NAME = "Atomic Wave"

    SPRITE_PATH = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Schrödinger/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Schrödinger/attack.png"
    SPRITE_SKILL = "assets/images/charactor/Schrödinger/skill.png"

    SPRITE_SCALE = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Atomic Wave", "ProjectileSkill", 18, 22, 3.5),
        "cc": ("Interference Well", "SummonZoneSkill", 17, 32, 7.0),
        "enhance": ("Superposition Domain", "DomainUltimateSkill", 0, 0, 0.0),
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
        self.skills["skill_Q"] = AtomicWave()
        self.skills["skill_E"] = InterferenceWell()
        self.skills["skill_R"] = SchrodingerDomain()
        self.skills["skill_Q_domain"] = QuantumPacket()
        self.skills["skill_E_domain"] = ProbabilityCloud()

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
        return "Schrödinger"
