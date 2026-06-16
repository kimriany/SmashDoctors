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
