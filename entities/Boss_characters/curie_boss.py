import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss


class CurieBoss(ConceptBoss):
    DISPLAY_NAME = "Curie Boss"
    SPRITE_IDLE = "assets/images/charactor/Curie/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/Curie/attack.png"
    SPRITE_JUMP = "assets/images/charactor/Curie/jump.png"
    SPRITE_SKILL = "assets/images/charactor/Curie/curie_radium_artifact.png"
    DOMAIN_BG_PATH = "assets/images/charactor/Curie/curie_domain.png"
    AURA_KIND = "rings"
    AURA_COLORS = ((150, 255, 96), (235, 255, 150))
    PROJECTILE_KIND = "radium"
    ZONE_KIND = "radiation"
    SPECIAL_KIND = "radiation"
    BASIC_LABEL = "RADIUM SHARD"
    ZONE_LABEL = "RADIATION FIELD"
    DASH_LABEL = "ION SHIFT"
    SPECIAL_LABEL = "MELTDOWN"

    def __init__(self, x, y, name="퀴리", player_id=2, max_hp=1320):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)
        self.color = (82, 150, 70)
        self.trim_color = (25, 74, 34)
        self.glow_color = (150, 255, 96)
        self.projectile_color = (140, 255, 90)
        self.projectile_core = (245, 255, 170)
        self.zone_color = (108, 240, 120)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color
        self.profile_key = "curie"
        self.WALK_SPEED = 2.05

    def _spawn_concept_projectiles(self, count=3, spread=0.5, damage=None, speed=None, size=None):
        for i, offset in enumerate((-0.32, 0.0, 0.32)):
            self._spawn_projectile(
                speed=4.7 + i * 0.18,
                damage=15 if damage is None else damage,
                delay=i * 7,
                angle_offset=offset,
                orbit=58 + i * 7,
                size=18 + i * 2,
                kind="radium",
            )

    def _spawn_concept_zones(self):
        for i, ox in enumerate((-135, 0, 135)):
            self._spawn_zone_on_target(
                118 + i * 12,
                102,
                warn=30 + i * 9,
                active=38,
                damage=12,
                offset_x=ox,
                kind="radiation",
            )

    def _spawn_concept_special(self, psys=None):
        for i in range(6 if self.domain_active else 5):
            self._spawn_zone_on_target(
                128 + i * 8,
                112,
                warn=24 + i * 8,
                active=42,
                damage=13,
                offset_x=random.randint(-230, 230),
                kind="radiation",
            )
        self._spawn_projectile(speed=3.8, damage=23, orbit=76, size=30, life=185, kind="radium")
