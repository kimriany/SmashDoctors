import math
import os
import random

import pygame

from entities.boss import Boss
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from systems.font_manager import font


class HoraBoss(Boss):
    DISPLAY_NAME = "Future Hora"
    DOMAIN_BG_PATH = "assets/images/charactor/Hora/hora_domain.png"
    DOMAIN_PARTICLE_COLOR = (80, 205, 255)
    BACKGROUND_PATH = "assets/images/charactor/Hora/hora_boss_background.png"
    STORY_DOMAIN_RULES = {
        "final_lock": True,
        "boss_phase2_hp_ratio": 0.68,
        "boss_domain_start_hp_ratio": 0.36,
        "boss_domain_hp": 180.0,
        "counter_domain_delay_frames": 8 * 60,
        "double_domain_break_delay_frames": 14 * 60,
        "double_domain_break_boss_hp_ratio": 0.12,
        "finisher_ready_on_break": True,
    }

    def __init__(self, x, y, name="미래의 Hora", player_id=2, max_hp=2400):
        super().__init__(SCREEN_WIDTH // 2 - 80, 178, name=name, player_id=player_id, max_hp=max_hp)
        self.rect.w = 160
        self.rect.h = 190
        self.color = (52, 120, 190)
        self.trim_color = (20, 36, 72)
        self.glow_color = (90, 210, 255)
        self.dark_color = (4, 12, 28)
        self.projectile_color = (90, 210, 255)
        self.projectile_core = (245, 250, 255)
        self.zone_color = (80, 175, 255)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.DOMAIN_PARTICLE_COLOR
        self.profile_key = "hora"
        self.WALK_SPEED = 0.0
        self._kb_resist = 1.0
        self.draw_as_background = True
        self.targetable = False
        self.vulnerable_timer = 0
        self.vulnerable_total = 0
        self.vulnerable_attack_damage_multiplier = 2.0
        self.vulnerable_skill_damage_multiplier = 2.0
        self.vulnerable_max_damage_per_hit = 150.0
        self.vulnerable_damage_budget = 600.0
        self.vulnerable_damage_taken = 0.0
        self.pattern_cooldown = 72
        self._cycle_step = 0
        self._frame = 0
        self._background_img = None
        self._vulnerable_img = None
        self._vulnerable_cache = {}
        self._background_failed = False
        self._last_safe_rect = self.rect.copy()
        self._target_history = []

    def configure_profile(self, profile):
        return

    def update(self, dt, platforms, event_bus, psys=None):
        if self.dead:
            return
        if self.invincible > 0:
            self.invincible -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.stagger_timer > 0:
            self.stagger_timer -= 1
        if self.weakened_timer > 0:
            self.weakened_timer -= 1
        self.bob_t += 0.04
        self.shake_x *= 0.68
        self.shake_y *= 0.68
        self._sync_hitbox()

    def ai_update(self, target, platforms, event_bus, psys=None):
        if self.dead:
            return

        self.target = target
        self._platforms = platforms or []
        self._frame += 1
        self._record_target_history(target)
        self._update_phase()

        was_targetable = self.targetable
        if self.vulnerable_timer > 0:
            self.vulnerable_timer -= 1
        self.targetable = self.vulnerable_timer > 0
        self._sync_hitbox()

        if self.targetable:
            self._clear_attack_patterns()
            self._keep_target_out_of_hitbox(target)
            return

        if was_targetable and not self.targetable:
            self.pattern_cooldown = max(self.pattern_cooldown, 120)

        self._update_pattern_objects(target, event_bus, psys)

        if self.cast_timer > 0:
            self.cast_timer -= 1
            if self.cast_timer <= 0:
                self._resolve_hora_cast(psys)
            return

        self.pattern_cooldown -= 1
        if self.pattern_cooldown <= 0:
            self._choose_hora_pattern()

    def take_damage(self, damage):
        if not self.targetable:
            return
        super().take_damage(damage)
        self.invincible = min(self.invincible, 2)
        self.vulnerable_timer = max(self.vulnerable_timer, 70)
        self.targetable = self.vulnerable_timer > 0

    def modify_incoming_damage(self, damage, attacker=None, data=None):
        if not self.targetable:
            return 0.0
        remaining = self.vulnerable_damage_budget - self.vulnerable_damage_taken
        if remaining <= 0:
            return 0.0
        data = data or {}
        multiplier = (
            self.vulnerable_skill_damage_multiplier
            if bool(data.get("is_skill", False))
            else self.vulnerable_attack_damage_multiplier
        )
        scaled = min(float(damage) * multiplier, self.vulnerable_max_damage_per_hit)
        applied = min(scaled, remaining)
        self.vulnerable_damage_taken += applied
        return applied

    def apply_knockback(self, attacker, damage, camera=None):
        if not self.targetable:
            return
        self.shake_x = 4 if attacker.rect.centerx < self.rect.centerx else -4
        self.shake_y = -2

    def _sync_hitbox(self):
        cx = SCREEN_WIDTH // 2
        top = 216 + int(math.sin(self._frame * 0.025) * 10)
        self.rect.update(cx - 118, top, 236, 260)
        self._last_safe_rect = self.rect.copy()

    def _choose_hora_pattern(self):
        actions = [
            ("starfall", "STAR CLOCK", 30, 102),
            ("chrono_barrage", "EDGE BARRAGE", 24, 96),
            ("clock_hands", "CLOCK HANDS", 30, 118),
            ("clock_field", "CLOCK FIELD", 28, 108),
            ("edge_crossfire", "PARADOX CROSS", 26, 112),
            ("time_lanes", "TIME LANES", 30, 120),
            ("orbit_burst", "ORBIT BURST", 28, 114),
            ("rewind_snare", "REWIND SNARE", 32, 126),
            ("vulnerable", "TIME PARADOX", 38, 178),
        ]
        if self.domain_active:
            actions.insert(6, ("second_hand_sweep", "SECOND HAND SWEEP", 34, 132))
            actions.insert(8, ("rewind_echoes", "REWIND ECHOES", 36, 138))

        index = self._cycle_step % len(actions)
        action, label, cast, cooldown = actions[index]
        self._cycle_step = (index + 1) % len(actions)
        self.cast_action = action
        self.cast_label = label
        self.cast_timer = cast
        self.cast_total = cast
        self.pattern_cooldown = cooldown

    def _resolve_hora_cast(self, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""
        if action == "starfall":
            self._spawn_starfall()
        elif action == "chrono_barrage":
            self._spawn_chrono_barrage()
        elif action == "clock_field":
            self._spawn_clock_field()
        elif action == "edge_crossfire":
            self._spawn_edge_crossfire()
        elif action == "clock_hands":
            self._spawn_clock_hands()
        elif action == "time_lanes":
            self._spawn_time_lanes()
        elif action == "orbit_burst":
            self._spawn_orbit_burst()
        elif action == "rewind_snare":
            self._spawn_rewind_snare()
        elif action == "second_hand_sweep":
            self._spawn_second_hand_sweep()
        elif action == "rewind_echoes":
            self._spawn_rewind_echoes()
        elif action == "vulnerable":
            self._open_vulnerable_window(psys)

    def _record_target_history(self, target):
        if target is None or target.dead:
            return
        self._target_history.append((self._frame, target.rect.centerx, target.rect.bottom))
        self._target_history = self._target_history[-360:]

    def _spawn_chrono_barrage(self):
        for wave in range(4 if not self.domain_active else 5):
            sources = self._edge_sources(wave, count=3)
            for i, (x, y) in enumerate(sources):
                self._schedule(
                    wave * 13 + i * 4,
                    self._aimed_projectile_from,
                    x,
                    y,
                    5.7 + wave * 0.18,
                    12,
                    16,
                    "time",
                    (i - 1) * 0.1,
                    170,
                )

    def _spawn_edge_crossfire(self):
        for wave in range(3 if not self.domain_active else 4):
            for i, (x, y) in enumerate(self._edge_sources(wave + 7, count=4)):
                self._schedule(
                    wave * 15 + i * 3,
                    self._aimed_projectile_from,
                    x,
                    y,
                    5.9 + (i % 2) * 0.38,
                    11,
                    14,
                    "quantum" if i % 2 else "time",
                    random.uniform(-0.12, 0.12),
                    150,
                )

    def _spawn_clock_field(self):
        if self.target is None:
            return
        bottom = self.target.rect.bottom
        offsets = (-210, 0, 210)
        for i, offset in enumerate(offsets):
            self._spawn_zone_at(
                self.target.rect.centerx + offset,
                bottom,
                105,
                105,
                warn=34 + i * 7,
                active=22,
                damage=12,
                kind="time",
                slow=True,
                slow_x=0.62,
                slow_y=0.82,
            )
        self._spawn_zone_at(
            SCREEN_WIDTH // 2,
            bottom,
            230,
            135,
            warn=62,
            active=28,
            damage=16,
            kind="gravity",
        )

    def _spawn_clock_hands(self):
        if self.target is None:
            return
        center_x = SCREEN_WIDTH // 2
        bottom = SCREEN_HEIGHT
        offsets = (-315, -105, 105, 315)
        for i, offset in enumerate(offsets):
            self._spawn_zone_at(
                center_x + offset,
                bottom,
                58,
                SCREEN_HEIGHT - 120,
                warn=38 + i * 8,
                active=18,
                damage=13,
                kind="time",
                slow=True,
                slow_x=0.76,
                slow_y=0.86,
            )
        self._spawn_zone_at(
            self.target.rect.centerx,
            self.target.rect.bottom,
            330,
            76,
            warn=78,
            active=22,
            damage=15,
            kind="gravity",
        )

    def _spawn_time_lanes(self):
        bottom = SCREEN_HEIGHT
        lanes = (150, 330, 510, 770, 950, 1130)
        parity = (self._cycle_step + self.phase) % 2
        for i, x in enumerate(lanes):
            if i % 2 != parity:
                continue
            self._spawn_zone_at(
                x,
                bottom,
                92,
                SCREEN_HEIGHT - 96,
                warn=42 + i * 5,
                active=26,
                damage=14,
                kind="time",
            )
        for wave in range(2 if not self.domain_active else 3):
            for i, (x, y) in enumerate(self._edge_sources(wave + 21, count=3)):
                self._schedule(
                    18 + wave * 18 + i * 5,
                    self._aimed_projectile_from,
                    x,
                    y,
                    5.2 + wave * 0.24,
                    10,
                    13,
                    "time",
                    random.uniform(-0.1, 0.1),
                    145,
                )

    def _spawn_orbit_burst(self):
        if self.target is None:
            return
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        count = 8 if not self.domain_active else 10
        for i in range(count):
            angle = math.tau * i / count
            x = cx + math.cos(angle) * (SCREEN_WIDTH * 0.56)
            y = cy + math.sin(angle) * (SCREEN_HEIGHT * 0.56)
            self._schedule(
                i * 4,
                self._aimed_projectile_from,
                x,
                y,
                4.9,
                10,
                13,
                "quantum" if i % 2 else "time",
                random.uniform(-0.09, 0.09),
                165,
            )

    def _spawn_second_hand_sweep(self):
        bottom = SCREEN_HEIGHT
        lane_w = 54
        steps = 7
        left_to_right = (self._cycle_step % 2) == 0
        xs = [130 + i * 170 for i in range(steps)]
        if not left_to_right:
            xs.reverse()

        for i, x in enumerate(xs):
            self._schedule(
                i * 11,
                self._spawn_zone_at,
                x,
                bottom,
                lane_w,
                SCREEN_HEIGHT - 92,
                28,
                18,
                14,
                "time",
                slow=True,
                slow_x=0.58,
                slow_y=0.78,
            )

        for i, (x, y) in enumerate(self._edge_sources(self._cycle_step + 47, count=4)):
            self._schedule(
                16 + i * 12,
                self._aimed_projectile_from,
                x,
                y,
                5.8,
                12,
                14,
                "quantum",
                random.uniform(-0.11, 0.11),
                155,
            )

    def _spawn_rewind_echoes(self):
        if not self._target_history:
            return
        snapshots = self._target_history[-300::60][-5:]
        if len(snapshots) < 3 and self.target is not None:
            snapshots.append((self._frame, self.target.rect.centerx, self.target.rect.bottom))

        for i, (_, x, bottom) in enumerate(reversed(snapshots)):
            self._schedule(
                i * 14,
                self._spawn_zone_at,
                x,
                bottom,
                148 + i * 8,
                118,
                34,
                24,
                13,
                "gravity" if i == 0 else "time",
                slow=True,
                slow_x=0.56,
                slow_y=0.78,
            )

        for wave in range(3):
            for i, (x, y) in enumerate(self._edge_sources(wave + 61, count=3)):
                self._schedule(
                    24 + wave * 18 + i * 5,
                    self._aimed_projectile_from,
                    x,
                    y,
                    5.3 + wave * 0.18,
                    11,
                    13,
                    "time",
                    random.uniform(-0.14, 0.14),
                    160,
                )

    def _spawn_rewind_snare(self):
        if self.target is None:
            return
        bottom = self.target.rect.bottom
        self._spawn_zone_at(
            self.target.rect.centerx,
            bottom,
            210,
            130,
            warn=34,
            active=25,
            damage=12,
            kind="gravity",
            pull=True,
        )
        for wave in range(3 if not self.domain_active else 4):
            sources = self._edge_sources(wave + 33, count=2)
            for i, (x, y) in enumerate(sources):
                self._schedule(
                    24 + wave * 16 + i * 7,
                    self._aimed_projectile_from,
                    x,
                    y,
                    5.5,
                    11,
                    14,
                    "time",
                    random.uniform(-0.12, 0.12),
                    160,
                )

    def _spawn_starfall(self):
        bottom = 470
        if self._platforms:
            bottom = max(p.top for p in self._platforms)
        xs = [120, 240, 380, 520, 660, 800, 940, 1080, 1200]
        random.shuffle(xs)
        for i, x in enumerate(xs[:5 if not self.domain_active else 7]):
            self._schedule(
                i * 7,
                self._aimed_projectile_from,
                x,
                -44,
                5.4 + (i % 3) * 0.38,
                11,
                14,
                "time",
                random.uniform(-0.08, 0.08),
                150,
            )
            self._spawn_zone_at(
                x,
                bottom,
                64,
                240,
                warn=24 + i * 6,
                active=11,
                damage=12,
                kind="time",
            )

    def _edge_sources(self, seed, count=4):
        rng = random.Random(self._frame * 31 + seed * 97)
        positions = []
        bands = ("left", "right", "top", "bottom")
        for i in range(count):
            side = bands[(seed + i) % len(bands)]
            if side == "left":
                positions.append((-48, rng.randint(115, SCREEN_HEIGHT - 110)))
            elif side == "right":
                positions.append((SCREEN_WIDTH + 48, rng.randint(115, SCREEN_HEIGHT - 110)))
            elif side == "top":
                positions.append((rng.randint(80, SCREEN_WIDTH - 80), -48))
            else:
                positions.append((rng.randint(80, SCREEN_WIDTH - 80), SCREEN_HEIGHT + 48))
        return positions

    def _open_vulnerable_window(self, psys=None):
        self._clear_attack_patterns()
        self.cast_action = None
        self.cast_label = ""
        self.cast_timer = 0
        self.cast_total = 0
        self.vulnerable_total = 260
        self.vulnerable_timer = self.vulnerable_total
        self.vulnerable_damage_taken = 0.0
        self.targetable = True
        self.invincible = 0
        self._sync_hitbox()
        if psys:
            psys.spawn(self.rect.centerx, self.rect.centery, self.glow_color, count=42, speed=7, life=38, r=5, glow=True)

    def _clear_attack_patterns(self):
        self.projectiles.clear()
        self.zones.clear()
        self._scheduled_actions.clear()

    def resolve_target_body_collision(self, target, platforms=None):
        if not self.targetable:
            return
        self._keep_target_out_of_hitbox(target)

    def _keep_target_out_of_hitbox(self, target):
        if target is None or target.dead or not self.rect.colliderect(target.rect):
            return

        overlap_left = target.rect.right - self.rect.left
        overlap_right = self.rect.right - target.rect.left
        overlap_top = target.rect.bottom - self.rect.top
        overlap_bottom = self.rect.bottom - target.rect.top
        smallest = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        if smallest == overlap_left:
            target.rect.right = self.rect.left
            if target.vel.x > 0:
                target.vel.x = 0
        elif smallest == overlap_right:
            target.rect.left = self.rect.right
            if target.vel.x < 0:
                target.vel.x = 0
        elif smallest == overlap_top:
            target.rect.bottom = self.rect.top
            if target.vel.y > 0:
                target.vel.y = 0
            target.on_ground = True
            target.jump_count = 0
        else:
            target.rect.top = self.rect.bottom
            if target.vel.y < 0:
                target.vel.y = 0

    def draw_background_layer(self, screen, camera):
        self._draw_cosmic_decor(screen)
        image = self._load_background_image()
        if image is None:
            self._draw_fallback_silhouette(screen)
            return

        height = int(SCREEN_HEIGHT * 0.94)
        width = int(image.get_width() * (height / max(1, image.get_height())))
        scaled = pygame.transform.smoothscale(image, (width, height))
        alpha = 235 if self.domain_active else 215
        scaled.set_alpha(alpha)
        x = SCREEN_WIDTH // 2 - width // 2
        y = SCREEN_HEIGHT - height - 8
        screen.blit(scaled, (x, y))

    def draw(self, screen, camera):
        if self.dead:
            return
        self._draw_patterns(screen, camera)
        self._draw_vulnerable_hitbox(screen, camera)
        if self.cast_timer > 0 and self.cast_label:
            text = font(18, bold=True).render(self.cast_label, True, (210, 238, 255))
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 120))

    def _load_background_image(self):
        if self._background_img is not None or self._background_failed:
            return self._background_img
        if not os.path.exists(self.BACKGROUND_PATH):
            self._background_failed = True
            return None
        try:
            self._background_img = pygame.image.load(self.BACKGROUND_PATH).convert_alpha()
        except Exception as exc:
            print(f"[HoraBoss] image load failed: {self.BACKGROUND_PATH} / {exc}")
            self._background_failed = True
        return self._background_img

    def _load_vulnerable_image(self):
        if self._vulnerable_img is not None or self._background_failed:
            return self._vulnerable_img
        base = self._load_background_image()
        if base is None:
            return None
        self._vulnerable_img = base.copy()
        return self._vulnerable_img

    def _grayscale_surface(self, surface):
        if hasattr(pygame.transform, "grayscale"):
            return pygame.transform.grayscale(surface)
        gray = surface.copy()
        gray.lock()
        for y in range(gray.get_height()):
            for x in range(gray.get_width()):
                r, g, b, a = gray.get_at((x, y))
                v = int(r * 0.299 + g * 0.587 + b * 0.114)
                gray.set_at((x, y), (v, v, v, a))
        gray.unlock()
        return gray

    def _vulnerable_surface(self, size):
        key = (max(1, int(size[0])), max(1, int(size[1])))
        if key in self._vulnerable_cache:
            return self._vulnerable_cache[key]
        image = self._load_vulnerable_image()
        if image is None:
            return None
        scaled = pygame.transform.smoothscale(image, key)
        gray = self._grayscale_surface(scaled)
        gray.set_alpha(218)
        self._vulnerable_cache[key] = gray
        return gray

    def _draw_cosmic_decor(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        t = self._frame * 0.018
        for i, (cx, cy, radius) in enumerate(((215, 210, 96), (1010, 210, 112), (640, 340, 170))):
            col = (60, 170, 255, 52 if i < 2 else 34)
            pygame.draw.circle(overlay, col, (cx, cy), radius, 2)
            for tick in range(12):
                ang = t * (1 if i % 2 == 0 else -1) + tick * math.tau / 12
                x1 = cx + int(math.cos(ang) * (radius - 10))
                y1 = cy + int(math.sin(ang) * (radius - 10))
                x2 = cx + int(math.cos(ang) * (radius + 8))
                y2 = cy + int(math.sin(ang) * (radius + 8))
                pygame.draw.line(overlay, (90, 205, 255, 68), (x1, y1), (x2, y2), 1)
            hand_ang = t * 1.8 + i
            pygame.draw.line(
                overlay,
                (245, 210, 120, 92),
                (cx, cy),
                (cx + int(math.cos(hand_ang) * radius * 0.72), cy + int(math.sin(hand_ang) * radius * 0.72)),
                2,
            )

        for i in range(36):
            x = (i * 97 + int(self._frame * (0.4 + (i % 5) * 0.08))) % SCREEN_WIDTH
            y = 60 + ((i * 53) % 570)
            pulse = 0.55 + 0.45 * math.sin(self._frame * 0.045 + i)
            r = max(1, int(2 + pulse * 2))
            pygame.draw.circle(overlay, (90, 205, 255, int(90 + pulse * 90)), (x, y), r)
            if i % 7 == 0:
                pygame.draw.line(overlay, (245, 215, 145, 90), (x - 8, y), (x + 8, y), 1)
                pygame.draw.line(overlay, (245, 215, 145, 90), (x, y - 8), (x, y + 8), 1)

        screen.blit(overlay, (0, 0))

    def _draw_fallback_silhouette(self, screen):
        cx = SCREEN_WIDTH // 2
        cy = 310 + int(math.sin(self._frame * 0.03) * 8)
        pygame.draw.circle(screen, (20, 48, 92), (cx, cy), 120)
        pygame.draw.circle(screen, (90, 210, 255), (cx, cy), 122, 2)
        pygame.draw.circle(screen, (245, 215, 145), (cx, cy), 42, 2)

    def _draw_vulnerable_hitbox(self, screen, camera):
        if not self.targetable:
            return
        r = camera.apply_rect(self.rect)
        pulse = 0.5 + 0.5 * math.sin(self._frame * 0.24)
        image = self._vulnerable_surface((r.w, r.h))
        if image is None:
            self._draw_fallback_silhouette(screen)
            return

        glow = image.copy()
        glow.fill((70, 220, 255, int(86 + pulse * 72)), special_flags=pygame.BLEND_RGBA_MULT)
        for scale, alpha in ((1.14, 70), (1.08, 98), (1.03, 130)):
            gw = max(1, int(r.w * scale))
            gh = max(1, int(r.h * scale))
            aura = pygame.transform.smoothscale(glow, (gw, gh))
            aura.set_alpha(alpha)
            screen.blit(aura, (r.centerx - gw // 2, r.centery - gh // 2))

        screen.blit(image, (r.x, r.y))
        if self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0:
            flash = image.copy()
            flash.fill((255, 255, 255, 160), special_flags=pygame.BLEND_RGBA_ADD)
            screen.blit(flash, (r.x, r.y))

        label = font(13, bold=True).render("VULNERABLE", True, (240, 250, 255))
        screen.blit(label, (r.centerx - label.get_width() // 2, r.bottom + 4))
