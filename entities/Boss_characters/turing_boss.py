import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss


class TuringBoss(ConceptBoss):
    DISPLAY_NAME = "Turing Boss"
    SPRITE_IDLE = "assets/images/charactor/Turing/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/Turing/제목_없는_아트워크 46.png"
    SPRITE_JUMP = "assets/images/charactor/Turing/제목_없는_아트워크 47.png"
    SPRITE_SKILL = "assets/images/charactor/Turing/right_artifact_transparent.png"
    DOMAIN_BG_PATH = "assets/images/charactor/Turing/Turing_domain.jpeg"
    AURA_KIND = "rings"
    AURA_COLORS = ((80, 235, 190), (170, 240, 255))
    PROJECTILE_KIND = "logic"
    ZONE_KIND = "grid"
    SPECIAL_KIND = "geometry"
    BASIC_LABEL = "HACK VIRUS"
    ZONE_LABEL = "HALTING GRID"
    DASH_LABEL = "CODE SHIFT"
    SPECIAL_LABEL = "UNIVERSAL MACHINE"

    def __init__(self, x, y, name="Turing", player_id=2, max_hp=1280):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.color = (38, 142, 132)
        self.trim_color = (8, 60, 64)
        self.glow_color = (80, 235, 190)
        self.projectile_color = (75, 235, 190)
        self.projectile_core = (170, 240, 255)
        self.zone_color = (70, 210, 210)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color
        self.profile_key = "turing"
        self.WALK_SPEED = 2.15
        self._wander_x = x
        self._wander_rethink = 0
        self._cycle_step = 0
        self.pattern_cooldown = 90

    def _move_toward_combat_range(self, platforms):
        if not platforms:
            return super()._move_toward_combat_range(platforms)

        floor = self._platform_under_x(self.rect.centerx) or self._main_platform()
        if floor is None:
            return super()._move_toward_combat_range(platforms)

        self._wander_rethink -= 1
        needs_new_target = (
            abs(self.rect.centerx - self._wander_x) < 16
            or not (floor.left + 70 <= self._wander_x <= floor.right - 70)
        )
        if needs_new_target and self._wander_rethink <= 0:
            self._wander_x = random.randint(floor.left + 80, floor.right - 80)
            self._wander_rethink = 42

        dx = self._wander_x - self.rect.centerx
        self.vel.x += ((1 if dx > 0 else -1) * self.WALK_SPEED - self.vel.x) * 0.045
        if abs(dx) < 20:
            self.vel.x *= 0.72
        if self.target and abs(self.target.rect.centerx - self.rect.centerx) > 30:
            self.facing = 1 if self.target.rect.centerx > self.rect.centerx else -1

    def _spawn_concept_projectiles(self, count=3, spread=0.45, damage=None, speed=None, size=None):
        for i, offset in enumerate((-0.28, 0.0, 0.28)):
            self._spawn_projectile(
                speed=5.1 + i * 0.25,
                damage=14 if damage is None else damage,
                delay=i * 6,
                angle_offset=offset,
                orbit=48 + i * 7,
                size=18,
                kind="logic",
            )

    def _choose_next_pattern(self):
        actions = (
            ("logic_probe", "HACK VIRUS", 26, 76),
            ("halting_grid", "HALTING GRID", 32, 92),
            ("code_shift", "CODE SHIFT", 24, 88),
            ("universal_machine", "UNIVERSAL MACHINE", 44, 150),
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
        if action == "logic_probe":
            self._spawn_concept_projectiles()
            return
        if action == "halting_grid":
            self._spawn_concept_zones()
            return
        if action == "code_shift":
            self._teleport_behind_target(psys)
            self._spawn_zone_at(self.rect.centerx + self.facing * 80, self.rect.bottom,
                                180, 150, warn=18, active=24, damage=18,
                                kind="grid", slow=True, slow_x=0.55)
            if psys:
                psys.spawn(self.rect.centerx, self.rect.centery, self.glow_color,
                           count=26, speed=7, gravity=0, life=28, r=5, glow=True)
            return
        if action == "universal_machine":
            self._spawn_concept_special(psys)
            return
        super()._resolve_cast(event_bus, psys)

    def _spawn_concept_zones(self):
        for i, ox in enumerate((-180, -90, 0, 90, 180)):
            self._spawn_zone_on_target(
                82,
                235,
                warn=28 + i * 5,
                active=14,
                damage=15,
                offset_x=ox,
                kind="grid",
            )

    def _spawn_concept_special(self, psys=None):
        self._spawn_concept_zones()
        for i, offset in enumerate((-0.46, -0.18, 0.18, 0.46)):
            self._spawn_projectile(
                speed=4.9,
                damage=13,
                delay=18 + i * 5,
                angle_offset=offset,
                orbit=52 + i * 7,
                size=17,
                kind="logic",
            )
