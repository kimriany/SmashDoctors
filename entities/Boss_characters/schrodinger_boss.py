import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss


class SchrodingerBoss(ConceptBoss):
    DISPLAY_NAME = "Schrodinger Boss"
    SPRITE_IDLE = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/Schrödinger/attack.png"
    SPRITE_JUMP = "assets/images/charactor/Schrödinger/jump.png"
    SPRITE_SKILL = "assets/images/charactor/Schrödinger/skill.png"
    DOMAIN_BG_PATH = "assets/images/charactor/Schrödinger/schrodinger_domain.png"
    AURA_KIND = "rings"
    AURA_COLORS = ((170, 120, 255), (105, 230, 255))
    PROJECTILE_KIND = "quantum"
    ZONE_KIND = "zone"
    SPECIAL_KIND = "quantum"
    BASIC_LABEL = "WAVE PACKET"
    ZONE_LABEL = "CAT BOX"
    DASH_LABEL = "QUANTUM LEAP"
    SPECIAL_LABEL = "SUPERPOSITION"

    def __init__(self, x, y, name="슈뢰딩거", player_id=2, max_hp=1360):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.color = (120, 76, 190)
        self.trim_color = (48, 24, 96)
        self.glow_color = (170, 120, 255)
        self.projectile_color = (165, 120, 255)
        self.projectile_core = (105, 230, 255)
        self.zone_color = (150, 94, 255)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color
        self.profile_key = "schrodinger"
        self.WALK_SPEED = 2.2
        self.pattern_cooldown = 120

    def _choose_next_pattern(self):
        self.cast_action = "cat_cycle"
        self.cast_label = "CAT BOX"
        self.cast_timer = 24
        self.cast_total = 24
        self.pattern_cooldown = 360

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""
        if action == "cat_cycle":
            self._teleport_behind_target(psys)
            self._schedule(18, self._spawn_uncertain_box)
            self._schedule(86, self._spawn_cat_rain)
            return
        super()._resolve_cast(event_bus, psys)

    def _spawn_uncertain_box(self):
        if random.random() < 0.5:
            self._spawn_zone_at(self.rect.centerx + self.facing * 70, self.rect.bottom,
                                190, 150, warn=38, active=20, damage=24, kind="zone")
        else:
            self.afterimages.append({"rect": self.rect.inflate(80, 40), "life": 36})

    def _spawn_cat_rain(self):
        if not self.target:
            return
        for i in range(9):
            cx = self.target.rect.centerx + random.randint(-260, 260)
            self._spawn_zone_at(cx, self.target.rect.bottom, 64, 250,
                                warn=18 + i * 7, active=12, damage=12, kind="zone")

    def _spawn_concept_projectiles(self, count=4, spread=0.8, damage=None, speed=None, size=None):
        for i, offset in enumerate((-0.52, -0.17, 0.17, 0.52)):
            self._spawn_projectile(
                speed=4.8 + (i % 2) * 0.7,
                damage=13 if damage is None else damage,
                delay=i * 5,
                angle_offset=offset,
                orbit=42 + i * 8,
                size=17,
                kind="quantum",
            )

    def _spawn_concept_zones(self):
        self._teleport_behind_target()
        self._spawn_zone_on_target(164, 112, warn=30, active=24, damage=18, centered_on_self=True, kind="zone")

    def _spawn_concept_special(self, psys=None):
        self._teleport_behind_target(psys)
        for i, offset in enumerate((-0.72, -0.42, -0.14, 0.14, 0.42, 0.72)):
            self._spawn_projectile(
                speed=5.0,
                damage=12,
                delay=i * 4,
                angle_offset=offset,
                orbit=44 + i * 5,
                size=16,
                kind="quantum",
            )
        self._spawn_zone_on_target(190, 126, warn=38, active=28, damage=20, centered_on_self=True, kind="zone")
