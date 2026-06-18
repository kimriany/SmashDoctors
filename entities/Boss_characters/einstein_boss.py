import math
import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss, first_existing


class EinsteinBoss(ConceptBoss):
    DISPLAY_NAME = "Einstein Boss"
    SPRITE_IDLE = "assets/images/charactor/Einstein/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/Einstein/attack.png"
    SPRITE_JUMP = "assets/images/charactor/Einstein/jump.png"
    DOMAIN_BG_PATH = first_existing([
        "assets/images/charactor/Einstein/einstein_domain.png",
        "assets/images/Einstein_domain.jpeg",
    ])
    AURA_KIND = "rings"
    AURA_COLORS = ((120, 190, 255), (235, 250, 255))
    PROJECTILE_KIND = "gravity"
    ZONE_KIND = "gravity"
    SPECIAL_KIND = "gravity"
    BASIC_LABEL = "GRAVITY LASH"
    ZONE_LABEL = "EVENT HORIZON"
    DASH_LABEL = "RELATIVITY SHIFT"
    SPECIAL_LABEL = "SINGULARITY"

    def __init__(self, x, y, name="아인슈타인", player_id=2, max_hp=1500):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.color = (64, 100, 188)
        self.trim_color = (20, 34, 86)
        self.glow_color = (120, 190, 255)
        self.projectile_color = (95, 165, 255)
        self.projectile_core = (235, 250, 255)
        self.zone_color = (70, 115, 255)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color
        self.profile_key = "einstein"
        self.WALK_SPEED = 1.95
        self._cycle_step = 0
        self._clone_timer = 0
        self._clone_count = 0
        self._curve_timer = 0
        self._history = []
        self._final_collapse_cd = 0
        self._hora_mode = "hora" in name.lower() or "Hora" in name or "호라" in name
        self.pattern_cooldown = 70

        if self._hora_mode:
            self.profile_key = "hora"
            self.SPECIAL_LABEL = "CAUSAL COLLAPSE"
            self.glow_color = (210, 210, 255)
            self.projectile_color = (190, 210, 255)
            self.projectile_core = (255, 255, 255)
            self.zone_color = (170, 180, 255)

    def ai_update(self, target, platforms, event_bus, psys=None):
        self._history.append((self.rect.centerx, self.rect.bottom))
        self._history = self._history[-360:]
        if target:
            trail = getattr(target, "_hora_position_history", [])
            trail.append((target.rect.centerx, target.rect.bottom))
            target._hora_position_history = trail[-600:]
        super().ai_update(target, platforms, event_bus, psys)

    def _choose_next_pattern(self):
        if self._hora_mode:
            self._choose_hora_pattern()
            return

        if self.phase >= 4 and self._final_collapse_cd <= 0:
            self.cast_action = "time_collapse"
            self.cast_label = "TIME COLLAPSE"
            self.cast_timer = 58
            self.cast_total = 58
            self.pattern_cooldown = 220
            self._final_collapse_cd = 720
            return
        self._final_collapse_cd = max(0, self._final_collapse_cd - self.pattern_cooldown)

        actions = (
            ("light_collapse", "LIGHT COLLAPSE", 34, 120),
            ("light_collapse", "LIGHT COLLAPSE", 28, 120),
            ("light_collapse", "LIGHT COLLAPSE", 22, 90),
            ("relativity_field", "RELATIVITY FIELD", 38, 80),
            ("parallel_world", "PARALLEL WORLD", 46, 120),
            ("time_rewind", "TIME REWIND", 34, 90),
            ("time_stop_shift", "TIME STOP", 24, 80),
        )
        action, label, cast, cooldown = actions[self._cycle_step]
        if action == "parallel_world" and self.hp_ratio > 0.65 and self._clone_timer > 0:
            action, label, cast, cooldown = ("light_collapse", "LIGHT COLLAPSE", 26, 100)
        self._cycle_step = (self._cycle_step + 1) % len(actions)
        self.cast_action = action
        self.cast_label = label
        self.cast_timer = cast
        self.cast_total = cast
        self.pattern_cooldown = cooldown

    def _choose_hora_pattern(self):
        phase2 = self.hp_ratio <= 0.70
        phase3 = self.hp_ratio <= 0.40
        actions = ["memory_echo", "memory_echo", "time_jump", "time_rewind_player", "observer_rift", "loop_repeat"]
        if phase2:
            actions.insert(4, "causal_collapse")
        if phase3:
            actions.insert(0, "time_station")
        action = actions[self._cycle_step % len(actions)]
        self._cycle_step += 1
        labels = {
            "memory_echo": "MEMORY ECHO",
            "time_jump": "TIME JUMP",
            "time_rewind_player": "REWIND",
            "observer_rift": "OBSERVER",
            "loop_repeat": "LOOP",
            "causal_collapse": "CAUSAL COLLAPSE",
            "time_station": "TIME STATION",
        }
        self.cast_action = action
        self.cast_label = labels[action]
        self.cast_timer = 34 if action not in ("causal_collapse", "time_station") else 58
        self.cast_total = self.cast_timer
        self.pattern_cooldown = 90 if not phase2 else 70

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""
        if action == "light_collapse":
            self._curve_timer = max(self._curve_timer, 90)
            self._spawn_light_collapse()
        elif action == "relativity_field":
            self._spawn_relativity_field()
        elif action == "parallel_world":
            self._spawn_parallel_world()
        elif action == "time_rewind":
            self._time_rewind(psys)
        elif action == "time_stop_shift":
            self._time_stop_shift(psys)
        elif action == "time_collapse":
            self._time_collapse()
        elif action == "memory_echo":
            self._memory_echo()
        elif action == "time_jump":
            self._time_jump(psys)
        elif action == "time_rewind_player":
            self._time_rewind_player(psys)
        elif action == "observer_rift":
            self._observer_rift()
        elif action == "loop_repeat":
            self._loop_repeat()
        elif action == "causal_collapse":
            self._causal_collapse()
        elif action == "time_station":
            self._time_station()
        else:
            super()._resolve_cast(event_bus, psys)

    def _move_toward_combat_range(self, platforms):
        if self._clone_timer > 0:
            self._clone_timer -= 1
        else:
            self._clone_count = 0
        if self._curve_timer > 0:
            self._curve_timer -= 1
            if self.target:
                dx = self.target.rect.centerx - self.rect.centerx
                self.vel.x += (math.copysign(2.3, dx) - self.vel.x) * 0.035
                self.vel.y += math.sin(self._curve_timer * 0.12) * 0.08
                self.facing = 1 if dx > 0 else -1
                if self._curve_timer % 6 == 0:
                    ghost = self.rect.copy()
                    ghost.x -= int(self.vel.x * 5)
                    self.afterimages.append({"rect": ghost, "life": 18})
            return
        super()._move_toward_combat_range(platforms)

    def _spawn_light_collapse(self):
        if not self.target:
            return
        lead = int(self.target.vel.x * 18)
        for i in range(5):
            cx = self.target.rect.centerx + lead + (i - 2) * 62
            self._spawn_zone_at(cx, self.target.rect.bottom, 58, 360,
                                warn=max(14, 46 - i * 6), active=12,
                                damage=15 + i, kind="time")
        for c in range(self._clone_count):
            offset = -170 if c == 0 else 170
            self._schedule(18 + c * 12, self._spawn_clone_beam, offset)

    def _spawn_clone_beam(self, offset):
        if not self.target:
            return
        self._spawn_zone_at(self.target.rect.centerx + offset, self.target.rect.bottom,
                            48, 320, warn=22, active=10, damage=9, kind="time")

    def _spawn_relativity_field(self):
        self._spawn_zone_on_target(310, 230, warn=34, active=120, damage=7, kind="time")
        if self.zones:
            self.zones[-1].update({
                "tick_interval": 34,
                "slow": True,
                "slow_x": 0.62,
                "slow_y": 0.95,
                "jump_scale": random.choice((0.55, 1.35)),
            })

    def _spawn_parallel_world(self):
        self._clone_timer = 600
        self._clone_count = 2
        for ox in (-120, 120):
            ghost = self.rect.copy()
            ghost.x += ox
            self.afterimages.append({"rect": ghost, "life": 150})
        for i in range(2):
            self._schedule(i * 24, self._spawn_clone_beam, -150 if i == 0 else 150)

    def _time_rewind(self, psys=None):
        if self._history:
            old = self.rect.copy()
            x, bottom = self._history[max(0, len(self._history) - 300)]
            self.rect.centerx = x
            self.rect.bottom = bottom
            self.afterimages.append({"rect": old, "life": 34})
        self.hp = min(self.max_hp, self.hp + 90)
        self._clone_timer = 0
        self._clone_count = 0
        self._spawn_zone_at(self.rect.centerx, self.rect.bottom, 240, 150,
                            warn=12, active=24, damage=18, kind="time")
        if psys:
            psys.spawn(self.rect.centerx, self.rect.centery, self.glow_color,
                       count=38, speed=8, gravity=-0.04, life=36, r=5, glow=True)

    def _time_stop_shift(self, psys=None):
        self.invincible = max(self.invincible, 46)
        if self.target:
            near = sorted(self._platforms, key=lambda p: abs(p.centerx - self.target.rect.centerx))
            platform = near[1] if len(near) > 1 else (near[0] if near else None)
            self._teleport_to_platform(platform, psys=psys)

    def _time_collapse(self):
        if not self.target:
            return
        trail = getattr(self.target, "_hora_position_history", [])[-480::48]
        for i, pos in enumerate(trail):
            x, bottom = pos
            self._spawn_zone_at(x, bottom, 76, 128, warn=20 + i * 8,
                                active=14, damage=13, kind="time")
        self._spawn_light_collapse()
        self.stagger_timer = max(self.stagger_timer, 60)

    def _memory_echo(self):
        if not self.target:
            return
        trail = getattr(self.target, "_hora_position_history", [])[-480::60]
        for i, (x, bottom) in enumerate(trail):
            self._spawn_zone_at(x, bottom, 68, 108, warn=28 + i * 10,
                                active=12, damage=10, kind="time")

    def _time_jump(self, psys=None):
        if len(self._history) > 180:
            old = self.rect.copy()
            x, bottom = self._history[-180]
            self.rect.centerx = x
            self.rect.bottom = bottom
            self.afterimages.append({"rect": old, "life": 34})
            if psys:
                psys.spawn(old.centerx, old.centery, self.glow_color, count=22, speed=7, life=28, r=4, glow=True)

    def _time_rewind_player(self, psys=None):
        if not self.target:
            return
        trail = getattr(self.target, "_hora_position_history", [])
        if len(trail) > 300:
            x, bottom = trail[-300]
            self.target.rect.centerx = x
            self.target.rect.bottom = bottom
            self.target.vel.x = 0
            self.target.vel.y = 0
            if psys:
                psys.spawn(x, bottom - 36, self.glow_color, count=30, speed=7, life=30, r=5, glow=True)

    def _observer_rift(self):
        if not self.target:
            return
        predict_x = self.target.rect.centerx + int(self.target.vel.x * 26)
        self._spawn_zone_at(predict_x, self.target.rect.bottom, 115, 185,
                            warn=30, active=22, damage=17, kind="time")

    def _loop_repeat(self):
        self._memory_echo()
        self._schedule(36, self._observer_rift)

    def _causal_collapse(self):
        main = self._main_platform()
        bottom = main.top if main else self.rect.bottom
        center = main.centerx if main else self.rect.centerx
        for i, ox in enumerate((-300, -180, -60, 60, 180, 300)):
            self._spawn_zone_at(center + ox, bottom, 82, 260,
                                warn=70 + i * 5, active=18, damage=18, kind="time")
        for p in self.projectiles:
            p["delay"] += 30
            p["retarget_at"] = p.get("age", 0) + 32

    def _time_station(self):
        main = self._main_platform()
        cx = main.centerx if main else self.rect.centerx
        bottom = main.top if main else self.rect.bottom
        self._spawn_zone_at(cx, bottom, 410, 300, warn=44, active=180,
                            damage=8, kind="time", tick_interval=40, slow=True, slow_x=0.72)
        self._schedule(90, self._time_jump)
        self._schedule(130, self._time_rewind_player)

    def _spawn_concept_projectiles(self, count=1, spread=0.0, damage=None, speed=None, size=None):
        self._spawn_projectile(
            speed=3.9 if speed is None else speed,
            damage=21 if damage is None else damage,
            delay=0,
            angle_offset=0.0,
            orbit=78,
            size=30 if size is None else size,
            life=195,
            kind="gravity",
        )

    def _spawn_concept_zones(self):
        self._spawn_zone_on_target(235, 168, warn=44, active=54, damage=16, kind="gravity")

    def _spawn_concept_special(self, psys=None):
        self._spawn_zone_on_target(270, 190, warn=48, active=64, damage=18, kind="gravity")
        for i, offset in enumerate((-0.36, 0.0, 0.36)):
            self._spawn_projectile(
                speed=4.0 + i * 0.35,
                damage=15,
                delay=18 + i * 6,
                angle_offset=offset,
                orbit=54 + i * 8,
                size=20,
                kind="gravity",
            )
