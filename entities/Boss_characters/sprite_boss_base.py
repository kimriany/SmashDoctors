import math
import os
import random

import pygame

from entities.boss import Boss
from systems.font_manager import font


def first_existing(paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


def load_img(path):
    if not path or not os.path.exists(path):
        return None
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as exc:
        print(f"[SpriteBoss] image load failed: {path} / {exc}")
        return None


def _clamp_color_channel(value):
    try:
        return max(0, min(255, int(value)))
    except (TypeError, ValueError):
        return 255


def _rgb_color(color, fallback=(255, 255, 255)):
    if isinstance(color, pygame.Color):
        values = (color.r, color.g, color.b)
    else:
        try:
            values = tuple(color)
        except TypeError:
            values = fallback

    if len(values) < 3:
        values = fallback

    return tuple(_clamp_color_channel(channel) for channel in values[:3])


def _rgba_color(color, alpha, fallback=(255, 255, 255)):
    return (*_rgb_color(color, fallback), _clamp_color_channel(alpha))


class SpriteBoss(Boss):
    SPRITE_IDLE = None
    SPRITE_ATTACK = None
    SPRITE_JUMP = None
    SPRITE_SKILL = None
    SPRITE_SCALE = 1.04
    SPRITE_SCALE_X = 1.04
    SPRITE_OFFSET_Y = 4

    AURA_KIND = "rings"
    AURA_COLORS = ((120, 220, 255), (255, 240, 160))

    def __init__(self, x, y, name="Boss", player_id=2, max_hp=1250):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.rect.w = 70
        self.rect.h = 94
        self.WALK_SPEED = 2.15
        self._movement_patience = random.randint(35, 70)

        self._sprites = {
            "idle": load_img(self.SPRITE_IDLE),
            "attack": load_img(self.SPRITE_ATTACK),
            "jump": load_img(self.SPRITE_JUMP),
            "skill": load_img(self.SPRITE_SKILL),
        }
        self._sprite_cache = {}

    def configure_profile(self, profile):
        return

    def _move_toward_combat_range(self, platforms):
        if self.target is None or self.target.dead:
            self.vel.x *= 0.82
            return

        dx = self.target.rect.centerx - self.rect.centerx
        dist = abs(dx)
        preferred = 235 if self.phase <= 2 else 280
        dead_zone = 88
        speed = self.WALK_SPEED + (0.12 if self.domain_active else 0.0)

        self._movement_patience -= 1
        if self._movement_patience <= 0:
            self._movement_patience = random.randint(42, 86)

        if dist > preferred + dead_zone:
            desired = math.copysign(speed, dx)
        elif dist < preferred - dead_zone:
            desired = -math.copysign(speed * 0.38, dx)
        else:
            desired = 0.0

        blend = 0.05 if desired else 0.038
        self.vel.x += (desired - self.vel.x) * blend
        if desired == 0.0:
            self.vel.x *= 0.88
        if abs(self.vel.x) < 0.10:
            self.vel.x = 0.0

        if abs(dx) > 86 and self.cast_timer <= 0 and self.dash_timer <= 0:
            self.facing = 1 if dx > 0 else -1

        if self.on_ground:
            ahead = pygame.Rect(
                self.rect.x + self.facing * (self.rect.w + 8),
                self.rect.bottom,
                10,
                8,
            )
            if not any(ahead.colliderect(p) for p in platforms):
                self.vel.x *= -0.28
                self.facing = -self.facing

    def _current_sprite_key(self):
        if self.cast_timer > 0 or self.dash_timer > 0 or self.attack_timer > 0:
            return "attack"
        if not self.on_ground or abs(self.vel.y) > 0.4:
            return "jump"
        return "idle"

    def draw(self, screen, camera):
        if self.dead:
            return

        self._draw_patterns(screen, camera)

        dr = self._get_draw_rect(camera)
        z = camera.zoom
        bob = int(math.sin(self.bob_t) * 2.2 * z) if self.on_ground else 0

        for img in self.afterimages:
            r = camera.apply_rect(img["rect"])
            a = int(88 * img["life"] / 28)
            sf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(sf, _rgba_color(self.glow_color, a), sf.get_rect(), border_radius=10)
            screen.blit(sf, (r.x, r.y))

        if self.on_ground:
            sh = pygame.Surface((dr.w + 12, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 86), sh.get_rect())
            screen.blit(sh, (dr.x - 6, dr.bottom - 5))

        if self.cast_timer > 0 or self.domain_active:
            self._draw_concept_aura(screen, camera, dr, bob)

        img = self._get_sprite(camera)
        if img is None:
            super().draw(screen, camera)
            return

        if self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0:
            img = img.copy()
            img.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)

        draw_x = dr.centerx - img.get_width() // 2
        draw_y = dr.bottom - img.get_height() + int(self.SPRITE_OFFSET_Y * z) + bob
        screen.blit(img, (draw_x, draw_y))

        if self.cast_timer > 0 and self.cast_label:
            txt = font(12, bold=True).render(self.cast_label, True, _rgb_color(self.glow_color))
            screen.blit(txt, (dr.centerx - txt.get_width() // 2, draw_y - 22))

    def _get_sprite(self, camera):
        key = self._current_sprite_key()
        img = self._sprites.get(key) or self._sprites.get("skill") or self._sprites.get("idle")
        if img is None:
            return None
        cache_key = (key, round(camera.zoom, 2), self.facing)
        if cache_key not in self._sprite_cache:
            w = max(1, int(self.rect.w * self.SPRITE_SCALE * self.SPRITE_SCALE_X * camera.zoom))
            h = max(1, int(self.rect.h * self.SPRITE_SCALE * camera.zoom))
            scaled = pygame.transform.smoothscale(img, (w, h))
            if self.facing == -1:
                scaled = pygame.transform.flip(scaled, True, False)
            self._sprite_cache[cache_key] = scaled
        return self._sprite_cache[cache_key]

    def _draw_concept_aura(self, screen, camera, dr, bob):
        elapsed = self.cast_total - self.cast_timer if self.cast_total else self.bob_t * 10
        surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        cx = dr.centerx
        cy = dr.centery + bob
        c1, c2 = (_rgb_color(color) for color in self.AURA_COLORS)

        if self.AURA_KIND == "helix":
            amp = int(28 * camera.zoom)
            height = int(130 * camera.zoom)
            a_pts, b_pts = [], []
            for i in range(16):
                t = i / 15
                y = cy - height // 2 + int(height * t)
                phase = elapsed * 0.16 + t * math.tau * 2.0
                x1 = cx + int(math.sin(phase) * amp)
                x2 = cx + int(math.sin(phase + math.pi) * amp)
                a_pts.append((x1, y))
                b_pts.append((x2, y))
                if i % 3 == 0:
                    pygame.draw.line(surf, _rgba_color(c2, 70), (x1, y), (x2, y), max(1, int(2 * camera.zoom)))
            pygame.draw.lines(surf, _rgba_color(c1, 130), False, a_pts, max(1, int(3 * camera.zoom)))
            pygame.draw.lines(surf, _rgba_color(c2, 115), False, b_pts, max(1, int(3 * camera.zoom)))
        else:
            for i in range(4):
                r = int((26 + i * 17 + math.sin(elapsed * 0.12 + i) * 4) * camera.zoom)
                col = c1 if i % 2 == 0 else c2
                pygame.draw.circle(surf, _rgba_color(col, 88 - i * 12), (cx, cy), max(4, r), max(1, int(2 * camera.zoom)))

        screen.blit(surf, (0, 0))


class ConceptBoss(SpriteBoss):
    PROJECTILE_KIND = "orb"
    ZONE_KIND = "zone"
    SPECIAL_KIND = "burst"
    SPECIAL_LABEL = "BOSS ART"

    BASIC_LABEL = "FOCUS ORB"
    ZONE_LABEL = "FIELD"
    DASH_LABEL = "SHIFT"

    PROJECTILE_SPEED = 5.2
    PROJECTILE_DAMAGE = 17
    PROJECTILE_SIZE = 20
    ZONE_DAMAGE = 17

    def _choose_next_pattern(self):
        options = ["concept_projectile", "concept_zone", "concept_dash"]
        if self.phase >= 2:
            options += ["concept_projectile", "concept_special"]
        if self.phase >= 3:
            options += ["concept_zone", "concept_special"]
        if self.phase >= 4:
            options += ["concept_special", "concept_projectile"]

        choice = random.choice(options)
        cast_frames = {
            "concept_projectile": 38,
            "concept_zone": 44,
            "concept_dash": 30,
            "concept_special": 58,
        }[choice]
        if self.domain_active:
            cast_frames = max(18, int(cast_frames * 0.75))

        labels = {
            "concept_projectile": self.BASIC_LABEL,
            "concept_zone": self.ZONE_LABEL,
            "concept_dash": self.DASH_LABEL,
            "concept_special": self.SPECIAL_LABEL,
        }
        self.cast_action = choice
        self.cast_label = labels[choice]
        self.cast_timer = cast_frames
        self.cast_total = cast_frames
        self.pattern_cooldown = 50 + random.randint(0, 32)

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""

        if action == "concept_projectile":
            self._spawn_concept_projectiles()
        elif action == "concept_zone":
            self._spawn_concept_zones()
        elif action == "concept_dash":
            self._spawn_concept_dash(psys)
        elif action == "concept_special":
            self._spawn_concept_special(psys)

    def _spawn_concept_projectiles(self, count=2, spread=0.42, damage=None, speed=None, size=None):
        damage = self.PROJECTILE_DAMAGE if damage is None else damage
        speed = self.PROJECTILE_SPEED if speed is None else speed
        size = self.PROJECTILE_SIZE if size is None else size
        if count <= 1:
            offsets = [0.0]
        else:
            offsets = [(-spread * 0.5) + spread * i / (count - 1) for i in range(count)]
        for i, offset in enumerate(offsets):
            self._spawn_projectile(
                speed=speed,
                damage=damage,
                delay=i * 5,
                angle_offset=offset,
                orbit=42 + i * 7,
                size=size,
                kind=self.PROJECTILE_KIND,
            )

    def _spawn_concept_zones(self):
        for i, ox in enumerate((-95, 95)):
            self._spawn_zone_on_target(
                118,
                96,
                warn=34 + i * 10,
                active=20,
                damage=self.ZONE_DAMAGE,
                offset_x=ox,
                kind=self.ZONE_KIND,
            )

    def _spawn_concept_dash(self, psys=None):
        for i in range(2):
            ghost = self.rect.copy()
            ghost.x -= self.facing * (36 + i * 28)
            self.afterimages.append({"rect": ghost, "life": 24 + i * 4})
        if psys:
            psys.spawn(self.rect.centerx, self.rect.centery, self.glow_color, count=22, speed=5.2, gravity=-0.02, life=28, r=5, glow=True)
        self.dash_timer = 20
        self.dash_has_hit = False
        self.vel.x = self.facing * (8.8 if self.domain_active else 7.6)

    def _spawn_concept_special(self, psys=None):
        kind = self.SPECIAL_KIND
        if kind == "radiation":
            for i in range(5):
                self._spawn_zone_on_target(126, 102, 28 + i * 10, 34, 13, offset_x=random.randint(-210, 210), kind=self.ZONE_KIND)
            self._spawn_concept_projectiles(count=1, damage=21, speed=4.4, size=25)
        elif kind == "quantum":
            self._teleport_behind_target(psys)
            self._spawn_concept_projectiles(count=6, spread=1.15, damage=12, speed=5.1, size=17)
            self._spawn_zone_on_target(168, 110, 34, 22, 18, centered_on_self=True, kind=self.ZONE_KIND)
        elif kind == "gravity":
            self._spawn_zone_on_target(235, 170, 46, 56, 17, kind="gravity")
            self._spawn_concept_projectiles(count=1, damage=24, speed=3.9, size=30)
        elif kind == "bomb":
            for i in range(5):
                self._spawn_zone_on_target(124, 96, 24 + i * 9, 18, 20, offset_x=random.randint(-220, 220), kind="bomb")
            self._spawn_concept_projectiles(count=3, spread=0.65, damage=15, speed=4.8, size=20)
        elif kind == "geometry":
            self._spawn_concept_projectiles(count=5, spread=0.82, damage=14, speed=5.7, size=18)
            for i in range(3):
                self._spawn_zone_on_target(122, 92, 34 + i * 8, 18, 16, offset_x=(i - 1) * 110, kind=self.ZONE_KIND)
        elif kind == "mutation":
            for i in range(5):
                self._spawn_zone_on_target(110 + i * 10, 86, 28 + i * 10, 20, 15, offset_x=random.randint(-180, 180), kind=self.ZONE_KIND)
            self._spawn_concept_projectiles(count=2, spread=0.52, damage=18, speed=4.8, size=22)
        elif kind == "time":
            self._spawn_zone_on_target(190, 130, 42, 44, 16, kind="gravity")
            self._spawn_concept_projectiles(count=4, spread=0.9, damage=13, speed=4.6, size=18)
        else:
            self._spawn_concept_projectiles(count=3, spread=0.7)
            self._spawn_zone_on_target(150, 104, 38, 20, 20, kind=self.ZONE_KIND)
