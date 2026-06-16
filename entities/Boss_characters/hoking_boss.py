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

    def __init__(self, x, y, name="호킹", player_id=2, max_hp=1450):
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
