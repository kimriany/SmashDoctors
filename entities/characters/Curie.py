"""
Curie — 라듐 결정과 방사능 구역으로 누적 피해를 만드는 캐릭터.

일반 스킬:
  Q / ;  Radium Shard     — ProjectileSkill, 초록빛 라듐 결정 투사체
  E / '  Radiation Field  — SummonZoneSkill, 방사능 오염 구역
  R / /  Radium Domain    — curie_domain.png 영역 전개

영역 전개 중 강화 스킬:
  Q / ;  Ion Lance        — 더 빠르고 관통감 있는 강화 투사체
  E / '  Meltdown Zone    — 넓은 다단 방사능 구역
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


ARTIFACT = "assets/images/charactor/Curie/curie_radium_artifact.png"
DOMAIN_BG = "assets/images/charactor/Curie/curie_domain.png"
RAD_COLORS = (
    (120, 255, 120),
    (190, 255, 120),
    (80, 230, 190),
    (245, 255, 210),
)


class _DomainOnlyMixin:
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


class RadiumShard(_NormalOnlyMixin, ProjectileSkill):
    DISPLAY_NAME = "Radium Shard"
    DESCRIPTION = "Throw a glowing radium crystal."
    ARTIFACT_PATH = ARTIFACT
    ICON_PATH = ARTIFACT
    PROJ_SPEED = 9.8
    PROJ_SIZE = 18
    PROJ_COLOR = (120, 255, 120)
    PROJ_GLOW = (210, 255, 160)
    COOLDOWN_SEC = 4.0

    def __init__(self):
        super().__init__("Radium Shard", damage=20, cooldown=240, duration=82)
        self.charge_value = 0.95

    def on_start(self, owner, event_bus=None, psys=None):
        self._px = float(owner.rect.centerx + owner.facing * 30)
        self._py = float(owner.rect.centery - 8)
        self._vx = self.PROJ_SPEED * owner.facing
        self._vy = -1.4
        self._alive = True
        if psys:
            psys.spawn(self._px, self._py, (120, 255, 120), count=16,
                       speed=4.5, gravity=-0.04, life=26, r=5, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive:
            return
        self._px += self._vx
        self._py += self._vy + math.sin(self.timer * 0.2) * 0.35
        self._vy *= 0.985
        if psys and self.timer % 3 == 0:
            psys.spawn(self._px - owner.facing * 12, self._py,
                       random.choice(RAD_COLORS), count=2, speed=2.2,
                       gravity=-0.04, life=20, r=3, glow=True)
        if abs(self._px - owner.rect.centerx) > 780:
            self._alive = False

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._alive = False
        target.vel.y -= 4
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.PROJ_GLOW,
                       count=28, speed=7, gravity=-0.05, life=32, r=5, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery, (80, 230, 190),
                       count=12, speed=4, gravity=-0.03, life=24, r=3, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active or not getattr(self, "_alive", False):
            return

        sx, sy = camera.world_to_screen(self._px, self._py)
        r = max(5, int(self.PROJ_SIZE * z))
        for i in range(3):
            rr = int(r * (1.9 - i * 0.35))
            surf = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (120, 255, 120, 42 - i * 8), (rr, rr), rr)
            screen.blit(surf, (sx - owner.facing * (i + 1) * r - rr, sy - rr),
                        special_flags=pygame.BLEND_RGBA_ADD)
        super().draw_front(owner, screen, camera, dr, bob, z)


class RadiationField(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Radiation Field"
    DESCRIPTION = "Contaminate floor tiles.\nEnemies standing on them take repeated damage."
    ICON_PATH = ARTIFACT
    WARN_FRAMES = 24
    ZONE_W = 220
    ZONE_H = 46
    ZONE_COLOR = (120, 255, 120)
    ZONE_GLOW = (220, 255, 130)
    COOLDOWN_SEC = 7.5
    TICK_INTERVAL = 24

    def __init__(self):
        super().__init__("Radiation Field", damage=7, cooldown=450, duration=150)
        self.charge_value = 1.2
        self._hit_timer = 0

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx - owner.rect.centerx) < 330:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 200
            self._zone_y = owner.rect.bottom
        self._hit_timer = 0

    def on_update(self, owner, event_bus=None, psys=None):
        active_phase = self.timer <= self.duration - self.WARN_FRAMES
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom)

        if active_phase:
            self._hit_timer += 1
            if self._hit_timer >= self.TICK_INTERVAL:
                self._hit_timer = 0
                self.has_hit = False

            target = getattr(owner, "_skill_target", None)
            if target and not target.dead:
                field = self.get_hitbox(owner)
                if field and field.colliderect(target.rect):
                    target.vel.x *= 0.86
                    target.vel.y *= 0.92

        if psys and self.timer % 5 == 0:
            for _ in range(4):
                psys.spawn(zx + random.randint(-self.ZONE_W // 2, self.ZONE_W // 2),
                           zy - random.randint(4, self.ZONE_H),
                           random.choice(RAD_COLORS), count=1, speed=1.2,
                           gravity=-0.05, life=18, r=random.randint(2, 4), glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.65
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW,
                       count=20, speed=5, gravity=-0.04, life=26, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom)
        sx, sy = camera.world_to_screen(zx, zy)
        warn = self.timer > self.duration - self.WARN_FRAMES
        t = self.timer / max(1, self.duration)
        zw = int(self.ZONE_W * z)
        zh = int(self.ZONE_H * z)
        pulse = math.sin(pygame.time.get_ticks() * 0.012)
        alpha = 68 if warn else max(34, int(86 * t))

        tile_w = max(16, int(28 * z))
        tile_h = max(8, int(14 * z))
        surf = pygame.Surface((zw + tile_w, zh + tile_h + int(24 * z)), pygame.SRCALPHA)
        base_y = int(20 * z)

        cols = max(1, zw // tile_w)
        for i in range(cols):
            x = i * tile_w + tile_w // 2
            jitter = int(math.sin(pulse + i * 0.8) * 3 * z)
            rect = pygame.Rect(x, base_y + jitter, tile_w + 2, tile_h)
            col = (95, 210, 70) if i % 2 == 0 else (120, 255, 120)
            pygame.draw.rect(surf, (*col, max(30, alpha - 10)), rect, border_radius=max(2, int(3 * z)))
            pygame.draw.rect(surf, (225, 255, 140, max(55, alpha)), rect, max(1, int(1 * z)),
                             border_radius=max(2, int(3 * z)))

            if i % 3 == 1:
                cx = rect.centerx
                cy = rect.centery
                r = max(2, int(5 * z))
                pygame.draw.circle(surf, (235, 255, 150, 110), (cx, cy), r, max(1, int(1 * z)))
                for a in (0, math.pi * 2 / 3, math.pi * 4 / 3):
                    p1 = (cx, cy)
                    p2 = (cx + math.cos(a - 0.35) * r * 1.8, cy + math.sin(a - 0.35) * r * 1.8)
                    p3 = (cx + math.cos(a + 0.35) * r * 1.8, cy + math.sin(a + 0.35) * r * 1.8)
                    pygame.draw.polygon(surf, (180, 255, 90, 60), (p1, p2, p3))

        pygame.draw.rect(
            surf,
            (120, 255, 120, 26 if not warn else 46),
            (tile_w // 2, base_y - int(8 * z), zw, zh + int(12 * z)),
            border_radius=max(3, int(6 * z)),
        )
        screen.blit(surf, (sx - surf.get_width() // 2, sy - base_y - tile_h))

    def get_hitbox(self, owner):
        if not self.active:
            return None
        if self.timer > self.duration - self.WARN_FRAMES:
            return None
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.bottom)
        return pygame.Rect(zx - self.ZONE_W // 2, zy - self.ZONE_H, self.ZONE_W, self.ZONE_H)


class CurieDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Radium Domain"
    DESCRIPTION = "Open Curie's radioactive domain."
    DOMAIN_BG_PATH = DOMAIN_BG
    DOMAIN_PARTICLE_COLOR = (150, 255, 120)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 32
    CUTSCENE_ZOOM = 1.44
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Radium Domain", damage=0, duration=999999)


class IonLance(_DomainOnlyMixin, RadiumShard):
    DISPLAY_NAME = "Ion Lance"
    DESCRIPTION = "Domain skill — fast ionized radium projectile."
    PROJ_SPEED = 14.0
    PROJ_SIZE = 22
    COOLDOWN_SEC = 3.0

    def __init__(self):
        ProjectileSkill.__init__(self, "Ion Lance", damage=34, cooldown=180, duration=76)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.8

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        self._vy = -0.4
        if psys:
            for _ in range(26):
                psys.spawn(self._px, self._py, random.choice(RAD_COLORS),
                           count=1, speed=random.uniform(3, 8), gravity=-0.06,
                           life=random.randint(18, 32), r=random.randint(3, 6), glow=True)


class MeltdownZone(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Meltdown Zone"
    DESCRIPTION = "Domain skill — large radioactive field with repeated hits."
    ICON_PATH = ARTIFACT
    WARN_FRAMES = 0
    ZONE_W = 230
    ZONE_H = 165
    ZONE_COLOR = (140, 255, 90)
    ZONE_GLOW = (230, 255, 120)
    COOLDOWN_SEC = 6.8
    MULTI_HIT_INTERVAL = 28

    def __init__(self):
        super().__init__("Meltdown Zone", damage=14, cooldown=408, duration=150)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.7
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
            psys.spawn(zx, zy, self.ZONE_GLOW, count=36, speed=8,
                       gravity=-0.08, life=42, r=7, glow=True)
            psys.spawn(zx, zy, (80, 255, 180), count=20, speed=5,
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
            for _ in range(5):
                psys.spawn(zx + random.randint(-self.ZONE_W // 2, self.ZONE_W // 2),
                           zy + random.randint(-self.ZONE_H // 2, self.ZONE_H // 2),
                           random.choice(RAD_COLORS), count=1, speed=1.8,
                           gravity=-0.05, life=22, r=random.randint(2, 5), glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x *= 0.6
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW,
                       count=26, speed=7, gravity=-0.05, life=28, r=5, glow=True)
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
        zw = int(self.ZONE_W * z)
        zh = int(self.ZONE_H * z)
        pulse = math.sin(pygame.time.get_ticks() * 0.012)

        surf = pygame.Surface((zw + 90, zh + 90), pygame.SRCALPHA)
        cx, cy = surf.get_width() // 2, surf.get_height() // 2
        pygame.draw.ellipse(surf, (80, 130, 25, 64), (45, 45, zw, zh))
        for i, mult in enumerate((1.0, 0.84, 0.68, 0.52, 0.36)):
            rect = pygame.Rect(0, 0, int(zw * mult + pulse * 8), int(zh * mult + pulse * 5))
            rect.center = (cx, cy)
            col = RAD_COLORS[i % len(RAD_COLORS)]
            pygame.draw.ellipse(surf, (*col, 118 - i * 14), rect, max(1, int(2 * z)))
        for i in range(6):
            ang = i * math.pi * 2 / 6 + pulse * 0.4
            x = cx + math.cos(ang) * zw * 0.34
            y = cy + math.sin(ang) * zh * 0.34
            pygame.draw.circle(surf, (240, 255, 180, 115), (int(x), int(y)), max(2, int(4 * z)))
        screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))


class Curie(Player):
    WEIGHT = 94
    KB_GROWTH = 82
    BASE_KB = 29
    WALK_SPEED = 6.1
    JUMP_POWER = -15.2
    MAX_JUMPS = 2
    ATTACK_DMG = 11
    ATK_FRAMES = 18
    ATK_CD = 30
    HIT_START = 3
    HIT_END = 14

    BODY_COLOR = (90, 210, 120)
    TRIM_COLOR = (35, 120, 65)
    GLOW_COLOR = (170, 255, 120)
    DARK_COLOR = (20, 80, 45)
    DISPLAY_NAME = "Curie"
    DESCRIPTION = (
        "Radioactive zoner with radium crystals.\n"
        "Domain turns radiation into repeated pressure."
    )
    PREVIEW_COLOR = (90, 210, 120)
    SKILL_NAME = "Radium Shard"

    SPRITE_PATH = "assets/images/charactor/Curie/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Curie/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Curie/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Curie/attack.png"
    SPRITE_SKILL = "assets/images/charactor/Curie/attack.png"

    SPRITE_SCALE = 1.25
    SPRITE_SCALE_X = 1.35
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Radium Shard", "ProjectileSkill", 20, 26, 4.0),
        "cc": ("Radiation Field", "SummonZoneSkill", 18, 34, 7.5),
        "enhance": ("Radium Domain", "DomainUltimateSkill", 0, 0, 0.0),
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
        self.skills["skill_Q"] = RadiumShard()
        self.skills["skill_E"] = RadiationField()
        self.skills["skill_R"] = CurieDomain()
        self.skills["skill_Q_domain"] = IonLance()
        self.skills["skill_E_domain"] = MeltdownZone()

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
        return "Curie"
