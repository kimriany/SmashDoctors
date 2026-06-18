import math
import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss, first_existing


class NewtonBoss(ConceptBoss):
    DISPLAY_NAME = "Newton Boss"
    SPRITE_IDLE = "assets/images/charactor/newton/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/newton/attack.png"
    SPRITE_JUMP = "assets/images/charactor/newton/jump.png"
    DOMAIN_BG_PATH = first_existing([
        "assets/images/charactor/newton/newton_domain.png",
        "assets/images/story/Newton.png",
    ])
    AURA_KIND = "rings"
    AURA_COLORS = ((95, 185, 255), (255, 235, 120))
    PROJECTILE_KIND = "gravity"
    ZONE_KIND = "zone"
    SPECIAL_KIND = "geometry"
    BASIC_LABEL = "GRAVITY APPLE"
    ZONE_LABEL = "CALCULUS FIELD"
    DASH_LABEL = "INERTIA STEP"
    SPECIAL_LABEL = "LAW OF MOTION"

    def __init__(self, x, y, name="뉴턴", player_id=2, max_hp=1400):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.color = (72, 126, 198)
        self.trim_color = (22, 48, 94)
        self.glow_color = (95, 185, 255)
        self.projectile_color = (95, 185, 255)
        self.projectile_core = (255, 235, 120)
        self.zone_color = (85, 170, 255)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color
        self.profile_key = "newton"
        self.WALK_SPEED = 2.0
        self._parabola_timer = 0
        self.pattern_cooldown = 90

    def _choose_next_pattern(self):
        self.cast_action = "newton_cycle"
        self.cast_label = "GRAVITY LAW"
        self.cast_timer = 30
        self.cast_total = 30
        self.pattern_cooldown = 360

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""
        if action == "newton_cycle":
            self._rise_and_drop()
            self._schedule(130, self._start_parabola)
            return
        super()._resolve_cast(event_bus, psys)

    def _move_toward_combat_range(self, platforms):
        if self._parabola_timer > 0:
            self._parabola_timer -= 1
            t = 1.0 - self._parabola_timer / 110
            direction = self.facing or 1
            self.vel.x = direction * 4.8
            self.vel.y = math.sin(t * math.pi * 2) * 1.8
            if self._parabola_timer % 8 == 0:
                self._spawn_zone_at(self.rect.centerx, self.rect.bottom + 30,
                                    88, 92, warn=20, active=20, damage=11, kind="bomb")
            return
        super()._move_toward_combat_range(platforms)

    def _rise_and_drop(self):
        main = self._main_platform()
        if main:
            x = self.target.rect.centerx if self.target else main.centerx
            self.rect.centerx = max(main.left + 90, min(main.right - 90, x))
            self.rect.bottom = main.top - 190
            self.vel.x = 0
            self.vel.y = 0
        for i in range(8):
            self._schedule(i * 14, self._drop_gravity_object, i)

    def _drop_gravity_object(self, index):
        if not self.target:
            return
        cx = self.target.rect.centerx + random.randint(-180, 180)
        damage = 15 if index % 2 else 22
        width = 72 if index % 2 else 96
        self._spawn_zone_at(cx, self.target.rect.bottom, width, 260,
                            warn=22, active=14, damage=damage, kind="bomb")

    def _start_parabola(self):
        self._parabola_timer = 110
        self.facing = 1 if not self.target or self.target.rect.centerx > self.rect.centerx else -1

    def _spawn_concept_projectiles(self, count=2, spread=0.28, damage=None, speed=None, size=None):
        for i, offset in enumerate((-0.18, 0.18)):
            self._spawn_projectile(
                speed=5.2 + i * 0.4,
                damage=17 if damage is None else damage,
                delay=i * 8,
                angle_offset=offset,
                orbit=50 + i * 9,
                size=21,
                kind="gravity",
            )

    def _spawn_concept_zones(self):
        for i, ox in enumerate((-150, 0, 150)):
            self._spawn_zone_on_target(
                104,
                142,
                warn=26 + i * 10,
                active=18,
                damage=18,
                offset_x=ox,
                kind="bomb",
            )

    def _spawn_concept_special(self, psys=None):
        for i, offset in enumerate((-0.5, -0.18, 0.18, 0.5)):
            self._spawn_projectile(
                speed=5.8,
                damage=15,
                delay=i * 5,
                angle_offset=offset,
                orbit=42,
                size=18,
                kind="gravity",
            )
        for ox in (-210, -70, 70, 210):
            self._spawn_zone_on_target(92, 160, warn=30 + abs(ox) // 20, active=18, damage=16, offset_x=ox, kind="bomb")
