import math
import random

import pygame

from entities.base_entity import BaseEntity
from systems.font_manager import font


class Boss(BaseEntity):
    """Story-mode HP boss with readable pattern attacks."""

    DISPLAY_NAME = "Story Boss"
    DOMAIN_BG_PATH = "assets/images/Einstein_domain.jpeg"
    DOMAIN_PARTICLE_COLOR = (255, 95, 80)
    PROFILES = {
        "default": {
            "body": (190, 58, 62),
            "trim": (95, 18, 26),
            "glow": (255, 110, 86),
            "dark": (62, 8, 15),
            "projectile": (255, 110, 82),
            "projectile_core": (255, 235, 210),
            "zone": (255, 95, 55),
            "domain_bg": "assets/images/Einstein_domain.jpeg",
            "domain_particle": (255, 95, 80),
            "special": "meteor",
            "special_label": "BOSS ART",
        },
        "einstein": {
            "body": (64, 100, 188),
            "trim": (20, 34, 86),
            "glow": (120, 190, 255),
            "dark": (8, 16, 44),
            "projectile": (95, 165, 255),
            "projectile_core": (235, 250, 255),
            "zone": (70, 115, 255),
            "domain_bg": "assets/images/Einstein_domain.jpeg",
            "domain_particle": (120, 190, 255),
            "special": "gravity_well",
            "special_label": "EVENT HORIZON",
        },
        "curie": {
            "body": (82, 150, 70),
            "trim": (25, 74, 34),
            "glow": (150, 255, 96),
            "dark": (10, 38, 18),
            "projectile": (140, 255, 90),
            "projectile_core": (245, 255, 170),
            "zone": (108, 240, 120),
            "domain_bg": "assets/images/charactor/Curie/curie_domain.png",
            "domain_particle": (140, 255, 90),
            "special": "radiation_field",
            "special_label": "RADIUM FIELD",
        },
        "nobel": {
            "body": (178, 82, 38),
            "trim": (84, 36, 18),
            "glow": (255, 150, 44),
            "dark": (52, 20, 8),
            "projectile": (255, 135, 34),
            "projectile_core": (255, 238, 110),
            "zone": (255, 105, 34),
            "domain_bg": "assets/images/charactor/Nobel/nobel_domain.png",
            "domain_particle": (255, 130, 35),
            "special": "bomb_barrage",
            "special_label": "MEGA BOMB",
        },
        "schrodinger": {
            "body": (120, 76, 190),
            "trim": (48, 24, 96),
            "glow": (170, 120, 255),
            "dark": (22, 10, 54),
            "projectile": (165, 120, 255),
            "projectile_core": (105, 230, 255),
            "zone": (150, 94, 255),
            "domain_bg": "assets/images/charactor/Schrödinger/schrodinger_domain.png",
            "domain_particle": (160, 120, 255),
            "special": "quantum_split",
            "special_label": "SUPERPOSITION",
        },
        "turing": {
            "body": (38, 142, 132),
            "trim": (8, 60, 64),
            "glow": (80, 235, 190),
            "dark": (2, 28, 30),
            "projectile": (75, 235, 190),
            "projectile_core": (170, 240, 255),
            "zone": (70, 210, 210),
            "domain_bg": "assets/images/charactor/Turing/Turing_domain.jpeg",
            "domain_particle": (80, 235, 190),
            "special": "logic_grid",
            "special_label": "BOMBE GRID",
        },
        "hoking": {
            "body": (44, 72, 150),
            "trim": (12, 20, 62),
            "glow": (78, 170, 255),
            "dark": (2, 6, 24),
            "projectile": (70, 150, 255),
            "projectile_core": (238, 250, 255),
            "zone": (52, 100, 220),
            "domain_bg": "assets/images/charactor/hoking/hoking_domain.png",
            "domain_particle": (80, 170, 255),
            "special": "singularity",
            "special_label": "SINGULARITY",
        },
        "pita": {
            "body": (72, 126, 198),
            "trim": (22, 48, 94),
            "glow": (95, 185, 255),
            "dark": (8, 18, 44),
            "projectile": (95, 185, 255),
            "projectile_core": (255, 235, 120),
            "zone": (85, 170, 255),
            "domain_bg": "assets/images/charactor/pita/domain.jpeg",
            "domain_particle": (95, 185, 255),
            "special": "geometry",
            "special_label": "GEOMETRY",
        },
        "darwin": {
            "body": (88, 136, 66),
            "trim": (38, 70, 30),
            "glow": (150, 220, 90),
            "dark": (18, 42, 16),
            "projectile": (150, 220, 90),
            "projectile_core": (245, 255, 180),
            "zone": (115, 190, 75),
            "domain_bg": "assets/images/story/nature.png",
            "domain_particle": (150, 220, 90),
            "special": "mutation",
            "special_label": "MUTATION",
        },
        "crick": {
            "body": (86, 132, 170),
            "trim": (28, 52, 92),
            "glow": (125, 225, 255),
            "dark": (10, 22, 42),
            "projectile": (110, 210, 255),
            "projectile_core": (245, 255, 210),
            "zone": (92, 190, 240),
            "domain_bg": "assets/images/story/Phylab.png",
            "domain_particle": (125, 225, 255),
            "special": "helix",
            "special_label": "DNA HELIX",
        },
    }

    def __init__(self, x, y, name="Boss", player_id=2, max_hp=1200):
        super().__init__(x, y, 78, 104, name)

        self.player_id = player_id
        self.max_hp = float(max_hp)
        self.hp = float(max_hp)
        self.final_lock = True

        self.stocks = 1
        self.spawn_x = x
        self.spawn_y = y

        self.color = (190, 58, 62)
        self.trim_color = (95, 18, 26)
        self.glow_color = (255, 110, 86)
        self.dark_color = (62, 8, 15)
        self.projectile_color = (255, 110, 82)
        self.projectile_core = (255, 235, 210)
        self.zone_color = (255, 95, 55)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.DOMAIN_PARTICLE_COLOR
        self.profile_key = "default"
        self.special_pattern = "meteor"
        self.special_label = "BOSS ART"

        self.attack_damage = 18
        self.ATTACK_DMG = 14
        self.WALK_SPEED = 2.15
        self.WEIGHT = 420
        self._kb_resist = 0.92

        self.target = None
        self.phase = 1
        self.pattern_cooldown = 80
        self.cast_timer = 0
        self.cast_total = 0
        self.cast_action = None
        self.cast_label = ""
        self.dash_timer = 0
        self.dash_has_hit = False
        self.stagger_timer = 0
        self.weakened_timer = 0

        self.projectiles = []
        self.zones = []
        self.afterimages = []
        self._zone_serial = 0
        self.skills = {}

        self.domain_active = False
        self.domain_locked = False
        self.domain_break_hits_taken = 0
        self.domain_break_hits_limit = 999
        self.domain_charge_stack = 0.0
        self.domain_charge_required = 1.0
        self.domain_ready = False
        self.finisher_charge_stack = 0.0
        self.finisher_charge_required = 999.0
        self.finisher_ready = False
        self.finisher_locked = True

        self.boss_domain_max_hp = 320.0
        self.boss_domain_hp = self.boss_domain_max_hp
        self.domain_broken = False

        self.bob_t = 0.0
        self.walk_t = 0.0

    def configure_profile(self, profile):
        text = ""
        if isinstance(profile, dict):
            text = " ".join(str(profile.get(k, "")) for k in ("class_path", "boss_name", "name"))
        elif profile is not None:
            text = str(profile)

        key = self._profile_key_from_text(text)
        cfg = self.PROFILES.get(key, self.PROFILES["default"])

        self.profile_key = key
        self.color = cfg["body"]
        self.trim_color = cfg["trim"]
        self.glow_color = cfg["glow"]
        self.dark_color = cfg["dark"]
        self.projectile_color = cfg["projectile"]
        self.projectile_core = cfg["projectile_core"]
        self.zone_color = cfg["zone"]
        self.domain_bg_path = cfg["domain_bg"]
        self.domain_particle_color = cfg["domain_particle"]
        self.special_pattern = cfg["special"]
        self.special_label = cfg["special_label"]

    def _profile_key_from_text(self, text):
        return self.profile_key_for(text)

    @classmethod
    def profile_key_for(cls, text):
        low = text.lower()
        checks = (
            ("einstein", "einstein"),
            ("curie", "curie"),
            ("nobel", "nobel"),
            ("schrödinger", "schrodinger"),
            ("schrodinger", "schrodinger"),
            ("turing", "turing"),
            ("hoking", "hoking"),
            ("hawking", "hoking"),
            ("pita", "pita"),
            ("pythagoras", "pita"),
            ("darwin", "darwin"),
            ("다윈", "darwin"),
            ("크릭", "crick"),
            ("crick", "crick"),
            ("cric", "crick"),
            ("ro2t", "turing"),
        )
        for token, key in checks:
            if token in low:
                return key
        return "default"

    def set_target(self, player):
        self.target = player

    def get_char_name(self):
        return self.name

    @property
    def hp_ratio(self):
        return max(0.0, self.hp / max(1.0, self.max_hp))

    def take_damage(self, damage):
        if self.dead or self.invincible > 0:
            return

        amount = float(damage)
        if self.weakened_timer > 0:
            amount *= 1.35

        next_hp = self.hp - amount
        self.hp = max(1.0 if self.final_lock else 0.0, next_hp)
        self.damage_pct = (1.0 - self.hp_ratio) * 100.0
        self.hit_flash = 16
        self.invincible = 5
        self.stagger_timer = max(self.stagger_timer, 6)

        if self.hp <= 0 and not self.final_lock:
            self.dead = True

    def apply_knockback(self, attacker, damage, camera=None):
        if self.dead:
            return
        dir_x = 1 if attacker.rect.centerx < self.rect.centerx else -1
        self.vel.x += dir_x * min(3.0, 0.08 * float(damage))
        self.vel.y = min(self.vel.y, -1.8)
        self.shake_x = dir_x * 5
        self.shake_y = -2

    def lose_stock(self, event_bus, killer=None, reason="finisher"):
        if self.dead:
            return
        self.stocks = 0
        self.hp = 0.0
        self.damage_pct = 100.0
        self.dead = True
        event_bus.emit("stock_lost", {
            "player": self,
            "killer": killer,
            "reason": reason,
        })
        event_bus.emit("entity_dead", {"entity": self})

    def check_skill_collision(self, target, event_bus, psys=None, fsys=None):
        """Pattern objects handle their own collisions during ai_update."""
        return

    def reset_domain_state(self):
        self.domain_active = False
        self.domain_locked = False
        self.domain_break_hits_taken = 0
        self.domain_break_hits_limit = 999
        self.domain_charge_stack = 0.0
        self.domain_ready = False
        self.finisher_charge_stack = 0.0
        self.finisher_ready = False
        self.finisher_locked = True

    def open_domain(self, event_bus):
        if self.dead or self.domain_active or self.domain_broken:
            return
        self.boss_domain_hp = self.boss_domain_max_hp
        event_bus.emit("domain_request", {
            "owner": self,
            "bg_path": self.domain_bg_path,
            "particle_color": self.domain_particle_color,
            "break_hits": 999,
            "cutscene_frames": 44,
            "cutscene_zoom": 1.5,
            "transition_speed": 0.038,
            "freeze_during_transition": True,
        })

    def ai_update(self, target, platforms, event_bus, psys=None):
        if self.dead:
            return

        self.target = target
        self._update_phase()
        self._update_pattern_objects(target, event_bus, psys)

        if self.stagger_timer > 0:
            self.stagger_timer -= 1
            self.vel.x *= 0.55
            return

        if self.weakened_timer > 0:
            self.weakened_timer -= 1
            self.vel.x *= 0.72
            return

        if self.cast_timer > 0:
            self.cast_timer -= 1
            self.vel.x *= 0.70
            if self.cast_timer <= 0:
                self._resolve_cast(event_bus, psys)
            return

        if self.dash_timer > 0:
            self._update_dash_attack(target, event_bus, psys)
            return

        self._move_toward_combat_range(platforms)

        if self.pattern_cooldown > 0:
            self.pattern_cooldown -= 1
            return

        self._choose_next_pattern()

    def _update_phase(self):
        ratio = self.hp_ratio
        if self.domain_broken or ratio <= 0.20:
            self.phase = 4
        elif ratio <= 0.50:
            self.phase = 3
        elif ratio <= 0.75:
            self.phase = 2
        else:
            self.phase = 1

    def _move_toward_combat_range(self, platforms):
        if self.target is None or self.target.dead:
            self.vel.x *= 0.72
            return

        dx = self.target.rect.centerx - self.rect.centerx
        dist = abs(dx)
        preferred = 205 if self.phase <= 2 else 260
        dead_zone = 82
        speed = self.WALK_SPEED + (0.18 if self.domain_active else 0.0)

        if dist > preferred + dead_zone:
            desired = math.copysign(speed, dx)
        elif dist < preferred - dead_zone:
            desired = -math.copysign(speed * 0.42, dx)
        else:
            desired = 0.0

        blend = 0.06 if desired else 0.04
        self.vel.x += (desired - self.vel.x) * blend
        if desired == 0.0:
            self.vel.x *= 0.86
        if abs(self.vel.x) < 0.10:
            self.vel.x = 0.0

        if abs(dx) > 82 and self.cast_timer <= 0 and self.dash_timer <= 0:
            self.facing = 1 if dx > 0 else -1

        if self.on_ground:
            ahead = pygame.Rect(
                self.rect.x + self.facing * (self.rect.w + 8),
                self.rect.bottom,
                10,
                8,
            )
            if not any(ahead.colliderect(p) for p in platforms):
                self.vel.x = 0
                self.facing = -self.facing

    def _choose_next_pattern(self):
        options = ["projectile", "zone", "dash"]
        if self.phase >= 2:
            options += ["teleport_strike", "fan_projectiles", "zone_projectile", "special"]
        if self.phase >= 3:
            options += ["fan_projectiles", "chasing_zones", "special"]
        if self.phase >= 4:
            options += ["dash", "zone_projectile", "fan_projectiles", "special"]

        choice = random.choice(options)
        cast_frames = {
            "projectile": 28,
            "zone": 34,
            "dash": 24,
            "teleport_strike": 34,
            "fan_projectiles": 42,
            "zone_projectile": 46,
            "chasing_zones": 52,
            "special": 58,
        }.get(choice, 30)

        if self.domain_active:
            cast_frames = max(18, int(cast_frames * 0.78))

        self.cast_action = choice
        self.cast_label = self.special_label if choice == "special" else choice.replace("_", " ").upper()
        self.cast_timer = cast_frames
        self.cast_total = cast_frames
        self.pattern_cooldown = 55 + random.randint(0, 35)

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""

        if action == "projectile":
            self._spawn_projectile(speed=7.2, damage=14)
        elif action == "zone":
            self._spawn_zone_on_target(118, 76, warn=42, active=16, damage=18)
        elif action == "dash":
            self.dash_timer = 20
            self.dash_has_hit = False
            self.vel.x = self.facing * (13.5 if self.domain_active else 11.0)
        elif action == "teleport_strike":
            self._teleport_behind_target(psys)
            self._spawn_zone_on_target(128, 86, warn=28, active=14, damage=20, centered_on_self=True)
        elif action == "fan_projectiles":
            self._spawn_fan_projectiles()
        elif action == "zone_projectile":
            self._spawn_zone_on_target(142, 86, warn=46, active=18, damage=20)
            self._spawn_projectile(speed=6.3, damage=12, delay=12)
        elif action == "chasing_zones":
            for i in range(3):
                self._spawn_zone_on_target(
                    108 + i * 14,
                    68,
                    warn=34 + i * 16,
                    active=14,
                    damage=15,
                    offset_x=(i - 1) * 72,
                )
        elif action == "special":
            self._resolve_special_pattern(psys)

    def _resolve_special_pattern(self, psys):
        special = self.special_pattern
        if special == "gravity_well":
            self._spawn_zone_on_target(220, 170, warn=44, active=58, damage=18, kind="gravity")
            self._spawn_projectile(speed=4.6, damage=16, orbit=52, size=24)
        elif special == "radiation_field":
            for i in range(4):
                self._spawn_zone_on_target(128, 96, warn=30 + i * 14, active=42, damage=12, offset_x=(i - 1.5) * 78, kind="radiation")
        elif special == "bomb_barrage":
            for i in range(5):
                self._spawn_zone_on_target(116, 92, warn=26 + i * 10, active=18, damage=20, offset_x=random.randint(-190, 190), kind="bomb")
            self._spawn_fan_projectiles(count=3, speed=4.8, damage=15, orbit=44)
        elif special == "quantum_split":
            self._teleport_behind_target(psys)
            self._spawn_fan_projectiles(count=6, speed=5.2, damage=13, orbit=36, spread=1.15)
            self._spawn_zone_on_target(150, 100, warn=34, active=22, damage=18, centered_on_self=True)
        elif special == "logic_grid":
            for i in range(5):
                self._spawn_zone_on_target(92, 250, warn=30 + i * 8, active=16, damage=16, offset_x=(i - 2) * 90, kind="grid")
            self._spawn_projectile(speed=5.4, damage=18, orbit=46, size=18)
        elif special == "singularity":
            self._spawn_projectile(speed=3.8, damage=26, orbit=76, size=30, life=190, kind="singularity")
            self._spawn_zone_on_target(230, 160, warn=54, active=36, damage=18, kind="gravity")
        elif special == "geometry":
            self._spawn_fan_projectiles(count=3, speed=5.8, damage=18, orbit=42, spread=0.0, angle_offsets=(-0.45, 0.0, 0.45))
            for i in range(3):
                self._spawn_zone_on_target(118, 88, warn=38 + i * 8, active=18, damage=16, offset_x=(i - 1) * 105)
        elif special == "mutation":
            for i in range(4):
                self._spawn_zone_on_target(112 + i * 12, 84, warn=30 + i * 14, active=20, damage=15, offset_x=random.randint(-160, 160), kind="radiation")
            self._spawn_projectile(speed=4.8, damage=18, orbit=50, size=22)
        elif special == "helix":
            self._spawn_fan_projectiles(count=2, speed=5.0, damage=17, orbit=54, spread=0.0, angle_offsets=(-0.22, 0.22))
            for i in range(4):
                self._spawn_zone_on_target(96, 82, warn=28 + i * 12, active=18, damage=14, offset_x=(i - 1.5) * 86, kind="grid")
        else:
            self._spawn_zone_on_target(160, 110, warn=42, active=22, damage=22)
            self._spawn_projectile(speed=5.2, damage=18, orbit=44)

    def _spawn_projectile(
        self,
        speed=7.0,
        damage=14,
        delay=0,
        angle_offset=0.0,
        orbit=38,
        size=None,
        life=160,
        kind="orb",
    ):
        if self.target is None:
            return
        sx = self.rect.centerx
        sy = self.rect.top - 34
        boost = 1.2 if self.domain_active else 1.0
        self.projectiles.append({
            "x": float(sx),
            "y": float(sy),
            "vx": 0.0,
            "vy": 0.0,
            "speed": speed * boost,
            "angle_offset": angle_offset,
            "state": "orbit",
            "orbit": int(orbit),
            "orbit_total": max(1, int(orbit)),
            "angle": random.uniform(0.0, math.tau),
            "orbit_radius": random.uniform(34.0, 58.0) + (8 if self.domain_active else 0),
            "orbit_speed": random.choice((-1, 1)) * random.uniform(0.105, 0.16),
            "r": size or (15 if not self.domain_active else 18),
            "damage": damage + (4 if self.domain_active else 0),
            "life": life,
            "delay": delay,
            "hit": False,
            "kind": kind,
        })

    def _spawn_fan_projectiles(self, count=None, speed=6.0, damage=12, orbit=38, spread=None, angle_offsets=None):
        count = count or (5 if not self.domain_active else 7)
        spread = (0.56 if count == 5 else 0.76) if spread is None else spread
        offsets = angle_offsets
        if offsets is None:
            offsets = []
            for i in range(count):
                t = 0.0 if count == 1 else i / (count - 1)
                offsets.append(-spread * 0.5 + spread * t)

        for i, offset in enumerate(offsets):
            self._spawn_projectile(
                speed=speed,
                damage=damage,
                delay=i * 3,
                angle_offset=offset,
                orbit=orbit + i * 3,
            )

    def _spawn_zone_on_target(
        self,
        w,
        h,
        warn,
        active,
        damage,
        offset_x=0,
        centered_on_self=False,
        kind="zone",
    ):
        if self.target is None:
            return
        if centered_on_self:
            cx = self.rect.centerx + self.facing * 55
            bottom = self.rect.bottom
        else:
            cx = self.target.rect.centerx + offset_x
            bottom = self.target.rect.bottom

        if self.domain_active:
            w = int(w * 1.18)
            damage += 4

        self._zone_serial += 1
        self.zones.append({
            "id": self._zone_serial,
            "rect": pygame.Rect(int(cx - w / 2), int(bottom - h), int(w), int(h)),
            "warn": warn,
            "active": active,
            "damage": damage,
            "hit": False,
            "kind": kind,
        })

    def _teleport_behind_target(self, psys=None):
        if self.target is None:
            return
        old = self.rect.copy()
        side = -1 if self.target.facing == 1 else 1
        self.rect.centerx = self.target.rect.centerx + side * 96
        self.rect.bottom = self.target.rect.bottom
        self.facing = -side
        self.afterimages.append({"rect": old, "life": 26})
        if psys:
            psys.spawn(old.centerx, old.centery, self.glow_color, count=18, speed=6, life=24, r=4, glow=True)
            psys.spawn(self.rect.centerx, self.rect.centery, self.glow_color, count=22, speed=6, life=26, r=5, glow=True)

    def _update_dash_attack(self, target, event_bus, psys):
        self.dash_timer -= 1
        self.vel.x *= 0.94
        if target is None or target.dead or target.invincible > 0 or self.dash_has_hit:
            return
        hitbox = self.rect.inflate(42, -12)
        if hitbox.colliderect(target.rect):
            self.dash_has_hit = True
            event_bus.emit("attack_hit", {
                "attacker": self,
                "target": target,
                "damage": 18 + (5 if self.domain_active else 0),
                "is_skill": True,
                "skill_type": "boss_dash",
                "particle_system": psys,
            })

    def _update_pattern_objects(self, target, event_bus, psys):
        alive_projectiles = []
        for p in self.projectiles:
            if p["delay"] > 0:
                p["delay"] -= 1
                alive_projectiles.append(p)
                continue

            if p.get("state") == "orbit":
                p["angle"] += p.get("orbit_speed", 0.12)
                anchor_x = self.rect.centerx
                anchor_y = self.rect.top - 34
                radius = p.get("orbit_radius", 46.0)
                p["x"] = anchor_x + math.cos(p["angle"]) * radius
                p["y"] = anchor_y + math.sin(p["angle"]) * radius * 0.42
                p["orbit"] -= 1
                if p["orbit"] <= 0 and target and not target.dead:
                    dx = target.rect.centerx - p["x"]
                    dy = target.rect.centery - p["y"]
                    base = math.atan2(dy, dx) + p.get("angle_offset", 0.0)
                    p["vx"] = math.cos(base) * p.get("speed", 6.0)
                    p["vy"] = math.sin(base) * p.get("speed", 6.0)
                    p["state"] = "fly"
                alive_projectiles.append(p)
                continue

            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            hit_rect = pygame.Rect(int(p["x"] - p["r"]), int(p["y"] - p["r"]), p["r"] * 2, p["r"] * 2)
            if target and not target.dead and target.invincible <= 0 and hit_rect.colliderect(target.rect):
                event_bus.emit("attack_hit", {
                    "attacker": self,
                    "target": target,
                    "damage": p["damage"],
                    "is_skill": True,
                    "skill_type": "boss_projectile",
                    "particle_system": psys,
                })
                continue
            if p["life"] > 0:
                alive_projectiles.append(p)
        self.projectiles = alive_projectiles

        alive_zones = []
        for z in self.zones:
            if z["warn"] > 0:
                z["warn"] -= 1
                if z.get("kind") == "gravity" and target and not target.dead:
                    self._pull_target_toward_zone(target, z["rect"], strength=0.055)
                alive_zones.append(z)
                continue
            if z["active"] > 0:
                z["active"] -= 1
                if z.get("kind") == "gravity" and target and not target.dead:
                    self._pull_target_toward_zone(target, z["rect"], strength=0.22)
                if target and not target.dead and target.invincible <= 0 and not z["hit"]:
                    if z["rect"].colliderect(target.rect):
                        z["hit"] = True
                        event_bus.emit("attack_hit", {
                            "attacker": self,
                            "target": target,
                            "damage": z["damage"],
                            "is_skill": True,
                            "skill_type": "boss_zone",
                            "particle_system": psys,
                        })
                alive_zones.append(z)
        self.zones = [z for z in alive_zones if z["warn"] > 0 or z["active"] > 0]

        for img in self.afterimages:
            img["life"] -= 1
        self.afterimages = [img for img in self.afterimages if img["life"] > 0]

    def _pull_target_toward_zone(self, target, rect, strength=0.12):
        dx = rect.centerx - target.rect.centerx
        dy = rect.centery - target.rect.centery
        dist = max(1.0, math.sqrt(dx * dx + dy * dy))
        target.vel.x += dx / dist * strength * 6.0
        target.vel.y += dy / dist * strength * 3.5

    def update(self, dt, platforms, event_bus, psys=None):
        if self.dead:
            return
        super().update(dt, platforms, event_bus)
        self.bob_t += 0.055
        if abs(self.vel.x) > 0.4:
            self.walk_t += 0.16

    def draw(self, screen, camera):
        if self.dead:
            return

        self._draw_patterns(screen, camera)

        dx, dy = self._get_draw_pos(camera)
        z = camera.zoom
        bob = int(math.sin(self.bob_t) * 2.8 * z) if self.on_ground else 0
        flash = self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0
        body = (255, 255, 255) if flash else self.color

        for img in self.afterimages:
            r = camera.apply_rect(img["rect"])
            a = int(90 * img["life"] / 26)
            sf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(sf, (*self.glow_color, a), sf.get_rect(), border_radius=12)
            screen.blit(sf, (r.x, r.y))

        if self.on_ground:
            sh = pygame.Surface((int(self.rect.w * z), 12), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 90), sh.get_rect())
            screen.blit(sh, (dx, dy + int(self.rect.h * z) - 4))

        aura = 0
        if self.cast_timer > 0:
            aura = int(85 + 85 * (1.0 - self.cast_timer / max(1, self.cast_total)))
        elif self.domain_active:
            aura = 70
        if aura:
            r = int((58 + math.sin(self.bob_t * 3) * 5) * z)
            sf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(sf, (*self.glow_color, aura), (r, r), r)
            screen.blit(sf, (dx + int(self.rect.w * z / 2) - r, dy + int(self.rect.h * z / 2) - r))

        leg_y = dy + int(self.rect.h * 0.72 * z) + bob
        swing = int(math.sin(self.walk_t) * 8 * z) if self.on_ground and abs(self.vel.x) > 0.4 else 0
        pygame.draw.rect(screen, self.trim_color, (dx + int(9 * z), leg_y - swing, int(20 * z), int(30 * z)), border_radius=max(3, int(4 * z)))
        pygame.draw.rect(screen, self.trim_color, (dx + int(49 * z), leg_y + swing, int(20 * z), int(30 * z)), border_radius=max(3, int(4 * z)))

        pygame.draw.rect(screen, body, (dx + int(5 * z), dy + int(30 * z) + bob, int(68 * z), int(48 * z)), border_radius=max(4, int(9 * z)))
        pygame.draw.rect(screen, self.trim_color, (dx + int(13 * z), dy + int(36 * z) + bob, int(13 * z), int(36 * z)), border_radius=max(2, int(4 * z)))
        pygame.draw.rect(screen, body, (dx + int(10 * z), dy + int(2 * z) + bob, int(58 * z), int(34 * z)), border_radius=max(5, int(12 * z)))

        horn_col = (255, 155, 118) if self.domain_active else self.trim_color
        for ox in (19, 59):
            pygame.draw.polygon(screen, horn_col, [
                (dx + int(ox * z), dy + int(6 * z) + bob),
                (dx + int((ox - 7) * z), dy - int(19 * z) + bob),
                (dx + int((ox + 7) * z), dy + int(6 * z) + bob),
            ])

        eye_x = dx + int((58 if self.facing == 1 else 20) * z)
        pygame.draw.circle(screen, (255, 50, 55), (eye_x, dy + int(19 * z) + bob), max(3, int(7 * z)))
        pygame.draw.circle(screen, (255, 225, 205), (eye_x, dy + int(16 * z) + bob), max(1, int(2 * z)))

        if self.cast_timer > 0 and self.cast_label:
            fnt = font(12, bold=True)
            txt = fnt.render(self.cast_label, True, (255, 190, 150))
            screen.blit(txt, (dx + int(self.rect.w * z / 2) - txt.get_width() // 2, dy - 28))

    def _get_draw_pos(self, camera):
        dr = self._get_draw_rect(camera)
        return dr.x, dr.y

    def _draw_patterns(self, screen, camera):
        for zdata in self.zones:
            r = camera.apply_rect(zdata["rect"])
            zcol = self._zone_draw_color(zdata)
            if zdata["warn"] > 0:
                pulse = 0.45 + 0.35 * math.sin(zdata["warn"] * 0.32)
                col = (*zcol, int(72 + 80 * pulse))
                pygame.draw.ellipse(screen, col, r, max(2, int(3 * camera.zoom)))
                fill = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                pygame.draw.ellipse(fill, (*zcol, 34), fill.get_rect())
                if zdata.get("kind") in ("grid", "bomb"):
                    pygame.draw.rect(fill, (*self.projectile_core, 55), fill.get_rect(), max(1, int(2 * camera.zoom)))
                screen.blit(fill, (r.x, r.y))
            else:
                fill = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                pygame.draw.ellipse(fill, (*zcol, 130), fill.get_rect())
                pygame.draw.ellipse(fill, (*self.projectile_core, 120), fill.get_rect(), max(2, int(4 * camera.zoom)))
                if zdata.get("kind") == "gravity":
                    for i in range(3):
                        inset = int((i + 1) * 10 * camera.zoom)
                        pygame.draw.ellipse(fill, (*self.projectile_core, 65 - i * 14), fill.get_rect().inflate(-inset, -inset), max(1, int(2 * camera.zoom)))
                screen.blit(fill, (r.x, r.y))

        for p in self.projectiles:
            if p["delay"] > 0:
                continue
            sx, sy = camera.world_to_screen(p["x"], p["y"])
            rr = max(4, int(p["r"] * camera.zoom))
            orbiting = p.get("state") == "orbit"
            pulse = 1.0
            if orbiting:
                total = max(1, p.get("orbit_total", 1))
                pulse = 0.75 + 0.35 * (1.0 - p.get("orbit", 0) / total)
            sf = pygame.Surface((rr * 4, rr * 4), pygame.SRCALPHA)
            pygame.draw.circle(sf, (*self.projectile_color, 76), (rr * 2, rr * 2), int(rr * 2 * pulse))
            pygame.draw.circle(sf, (*self.projectile_color, 220), (rr * 2, rr * 2), int(rr * pulse))
            pygame.draw.circle(sf, (*self.projectile_core, 215), (rr * 2, rr * 2), max(2, int(rr * 0.34 * pulse)))
            if orbiting:
                pygame.draw.circle(sf, (*self.projectile_core, 120), (rr * 2, rr * 2), int(rr * 1.5), max(1, rr // 5))
            screen.blit(sf, (sx - rr * 2, sy - rr * 2))

    def _zone_draw_color(self, zdata):
        kind = zdata.get("kind", "zone")
        if kind == "bomb":
            return (255, 100, 34)
        if kind == "radiation":
            return (135, 245, 95)
        if kind == "gravity":
            return (80, 120, 255)
        if kind == "grid":
            return (70, 220, 215)
        return self.zone_color
