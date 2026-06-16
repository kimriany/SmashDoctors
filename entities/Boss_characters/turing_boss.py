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

    def __init__(self, x, y, name="RO2T", player_id=2, max_hp=1280):
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
