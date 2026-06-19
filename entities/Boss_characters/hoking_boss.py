import math
import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss


class HokingBoss(ConceptBoss):
    DISPLAY_NAME = "Hoking Boss"
    SPRITE_IDLE = "assets/images/charactor/hoking/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/hoking/attack.png"
    SPRITE_JUMP = "assets/images/charactor/hoking/jump.png"
    SPRITE_SKILL = "assets/images/charactor/hoking/skill.png"
    DOMAIN_BG_PATH = "assets/images/charactor/hoking/hoking_domain.png"
    AURA_KIND = "rings"
    AURA_COLORS = ((78, 170, 255), (238, 250, 255))
    PROJECTILE_KIND = "singularity"
    ZONE_KIND = "gravity"
    SPECIAL_KIND = "time"
    BASIC_LABEL = "HAWKING SHARD"
    ZONE_LABEL = "TIME DILATION"
    DASH_LABEL = "HORIZON STEP"
    SPECIAL_LABEL = "ENTROPY HORIZON"

    def __init__(self, x, y, name="호킹", player_id=2, max_hp=2000):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.color = (44, 72, 150)
        self.trim_color = (12, 20, 62)
        self.glow_color = (78, 170, 255)
        self.projectile_color = (70, 150, 255)
        self.projectile_core = (238, 250, 255)
        self.zone_color = (52, 100, 220)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color
        self.profile_key = "hoking"
        self.WALK_SPEED = 1.9
        self._cycle_step = 0
        self._float_timer = 0
        self.pattern_cooldown = 60

    def _choose_next_pattern(self):
        actions = (
            ("hawking_radiation", "HAWKING RADIATION", 22, 60),
            ("hawking_radiation", "HAWKING RADIATION", 22, 60),
            ("hawking_radiation", "HAWKING RADIATION", 22, 60),
            ("horizon_step", "EVENT HORIZON", 36, 150),
            ("singularity_collapse", "SINGULARITY", 46, 100),
            ("float_phase", "ZERO-G DRIFT", 18, 120),
        )
        action, label, cast, cooldown = actions[self._cycle_step]
        self._cycle_step = (self._cycle_step + 1) % len(actions)
        self.cast_action = action
        self.cast_label = label
        self.cast_timer = cast
        self.cast_total = cast
        self.pattern_cooldown = cooldown

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""
        if action == "hawking_radiation":
            self._spawn_hawking_radiation()
        elif action == "horizon_step":
            self._horizon_step(psys)
        elif action == "singularity_collapse":
            self._singularity_collapse()
        elif action == "float_phase":
            self._float_timer = 120
            self.invincible = max(self.invincible, 20)
        else:
            super()._resolve_cast(event_bus, psys)

    def _move_toward_combat_range(self, platforms):
        if self._float_timer > 0:
            self._float_timer -= 1
            self.rect.y += int(math.sin(self._float_timer * 0.08) * 2)
            if self.target:
                dx = self.target.rect.centerx - self.rect.centerx
                self.vel.x += (math.copysign(1.7, dx) - self.vel.x) * 0.025
                self.facing = 1 if dx > 0 else -1
            self._kb_resist = 0.97
            return
        self._kb_resist = 0.92
        super()._move_toward_combat_range(platforms)

    def _spawn_hawking_radiation(self):
        origin_x = self.rect.centerx
        origin_y = self.rect.centery - 22
        for i in range(8):
            angle = i * math.tau / 8 + random.uniform(-0.12, 0.12)
            speed = random.uniform(3.6, 5.2)
            self.projectiles.append({
                "x": float(origin_x),
                "y": float(origin_y),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "speed": speed,
                "angle_offset": 0.0,
                "state": "fly",
                "orbit": 0,
                "orbit_total": 1,
                "angle": angle,
                "orbit_radius": 0,
                "orbit_speed": 0,
                "r": 14,
                "damage": 10,
                "life": 155,
                "delay": 0,
                "hit": False,
                "kind": "singularity",
                "age": 0,
                "retarget_at": 42,
                "retarget_boost": 1.45,
            })

    def _horizon_step(self, psys=None):
        if not self.target:
            return
        platforms = self._platforms or []
        candidates = [p for p in platforms if (p.centerx - self.target.rect.centerx) * (self.rect.centerx - self.target.rect.centerx) < 0]
        platform = max(candidates or platforms, key=lambda p: abs(p.centerx - self.target.rect.centerx), default=None)
        if platform:
            self._teleport_to_platform(platform, x=platform.centerx, psys=psys)
        self._spawn_zone_at(self.rect.centerx, self.rect.bottom + 20,
                            230, 190, warn=8, active=110, damage=7,
                            kind="gravity", tick_interval=28, slow=True, slow_x=0.75)
        self._spawn_zone_on_target(250, 210, warn=46, active=90, damage=8, kind="gravity")
        if self.zones:
            self.zones[-1].update({"tick_interval": 24, "slow": True, "slow_x": 0.58, "slow_y": 0.75})

    def _singularity_collapse(self):
        main = self._main_platform()
        cx = main.centerx if main else self.rect.centerx
        bottom = main.top if main else self.rect.bottom
        self._spawn_zone_at(cx, bottom, 320, 260, warn=70, active=44,
                            damage=28, kind="gravity")

    def _spawn_concept_projectiles(self, count=2, spread=0.38, damage=None, speed=None, size=None):
        for i, offset in enumerate((-0.2, 0.2)):
            self._spawn_projectile(
                speed=4.5 + i * 0.25,
                damage=16 if damage is None else damage,
                delay=i * 10,
                angle_offset=offset,
                orbit=66 + i * 14,
                size=22 + i * 3,
                kind="singularity",
            )

    def _spawn_concept_zones(self):
        self._spawn_zone_on_target(210, 138, warn=42, active=50, damage=14, kind="gravity")
        self._spawn_zone_on_target(126, 98, warn=30, active=24, damage=15, offset_x=-150, kind="gravity")
        self._spawn_zone_on_target(126, 98, warn=36, active=24, damage=15, offset_x=150, kind="gravity")

    def _spawn_concept_special(self, psys=None):
        self._spawn_projectile(speed=3.3, damage=26, orbit=84, size=34, life=210, kind="singularity")
        for ox in (-180, 0, 180):
            self._spawn_zone_on_target(144, 116, warn=36 + abs(ox) // 18, active=34, damage=16, offset_x=ox, kind="gravity")
