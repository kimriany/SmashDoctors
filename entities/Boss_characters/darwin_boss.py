import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss, first_existing


class DarwinBoss(ConceptBoss):
    DISPLAY_NAME = "Darwin Boss"
    SPRITE_IDLE = "assets/images/charactor/dawin/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/dawin/attack.png"
    SPRITE_JUMP = "assets/images/charactor/dawin/jump.png"
    DOMAIN_BG_PATH = first_existing([
        "assets/images/charactor/dawin/darwin_domain.png",
        "assets/images/story/nature.png",
    ])
    AURA_KIND = "rings"
    AURA_COLORS = ((150, 220, 90), (245, 255, 180))
    PROJECTILE_KIND = "spore"
    ZONE_KIND = "radiation"
    SPECIAL_KIND = "mutation"
    BASIC_LABEL = "SPORE SEED"
    ZONE_LABEL = "NATURAL SELECTION"
    DASH_LABEL = "ADAPTATION"
    SPECIAL_LABEL = "MUTATION BURST"

    def __init__(self, x, y, name="다윈", player_id=2, max_hp=150):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.color = (88, 136, 66)
        self.trim_color = (38, 70, 30)
        self.glow_color = (150, 220, 90)
        self.projectile_color = (150, 220, 90)
        self.projectile_core = (245, 255, 180)
        self.zone_color = (115, 190, 75)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color
        self.profile_key = "darwin"
        self.WALK_SPEED = 2.0
        self._ape_count = 0
        self.pattern_cooldown = 80

    def _move_toward_combat_range(self, platforms):
        self.vel.x *= 0.70
        if self.invincible > 0 and self.invincible % 8 == 0:
            ghost = self.rect.copy()
            ghost.x += random.randint(-8, 8)
            self.afterimages.append({"rect": ghost, "life": 14})

    def _choose_next_pattern(self):
        self.cast_action = "evolution" if self._ape_count < 3 else "devolution"
        self.cast_label = "EVOLUTION" if self._ape_count < 3 else "DEVOLUTION"
        self.cast_timer = 34
        self.cast_total = 34
        self.pattern_cooldown = 110

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""
        self.invincible = max(self.invincible, 60)
        self._schedule(55, self._teleport_to_random_platform, psys)
        if action == "evolution":
            self._ape_count += 1
            self._spawn_ape_sequence()
        elif action == "devolution":
            self._ape_count = 0
            self._apply_devolution(psys)
        else:
            super()._resolve_cast(event_bus, psys)

    def _teleport_to_random_platform(self, psys=None):
        platform = self._random_platform()
        self._teleport_to_platform(platform, psys=psys)

    def _spawn_ape_sequence(self):
        for i in range(10):
            self._schedule(i * 18, self._spawn_ape_shockwave, i)

    def _spawn_ape_shockwave(self, index):
        if not self.target:
            return
        side = -1 if index % 2 == 0 else 1
        cx = self.target.rect.centerx + side * random.randint(45, 110)
        bottom = self.target.rect.bottom
        self._spawn_zone_at(cx, bottom, 132, 72, warn=16, active=12, damage=9, kind="radiation")

    def _apply_devolution(self, psys=None):
        if not self.target:
            return
        self.target._speed_debuff_timer = max(getattr(self.target, "_speed_debuff_timer", 0), 1200)
        self.target._speed_debuff_mult = 0.52
        self.target._attack_lock_timer = max(getattr(self.target, "_attack_lock_timer", 0), 1200)
        self._spawn_zone_on_target(210, 190, warn=28, active=28, damage=12, kind="radiation")
        if psys:
            psys.spawn(self.target.rect.centerx, self.target.rect.centery, self.glow_color,
                       count=34, speed=7, gravity=-0.04, life=42, r=5, glow=True)

    def _spawn_concept_projectiles(self, count=2, spread=0.42, damage=None, speed=None, size=None):
        for i, offset in enumerate((-0.24, 0.18, 0.44)):
            self._spawn_projectile(
                speed=4.3 + i * 0.28,
                damage=14 if damage is None else damage,
                delay=i * 9,
                angle_offset=offset,
                orbit=62 + i * 10,
                size=17 + i * 3,
                kind="spore",
            )

    def _spawn_concept_zones(self):
        for i, ox in enumerate((-160, -45, 80, 175)):
            self._spawn_zone_on_target(
                88 + i * 18,
                82,
                warn=30 + i * 7,
                active=24,
                damage=14,
                offset_x=ox,
                kind="radiation",
            )

    def _spawn_concept_special(self, psys=None):
        for i in range(5):
            self._spawn_zone_on_target(
                102 + i * 16,
                84 + (i % 2) * 22,
                warn=25 + i * 10,
                active=26,
                damage=15,
                offset_x=random.randint(-210, 210),
                kind="radiation",
            )
        self._spawn_concept_projectiles(damage=17)
