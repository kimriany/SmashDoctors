from entities.Boss_characters.sprite_boss_base import ConceptBoss


class Ro2tBoss(ConceptBoss):
    DISPLAY_NAME = "Ro2t Boss"
    STORY_DOMAIN_RULES = {
        "final_lock": False,
        "boss_phase2_hp_ratio": 0.65,
        "boss_domain_start_hp_ratio": 0.35,
        "boss_domain_hp": 180.0,
        "counter_domain_delay_frames": 8 * 60,
        "double_domain_break_delay_frames": 12 * 60,
        "double_domain_break_boss_hp_ratio": 0.15,
        "finisher_ready_on_break": False,
    }

    SPRITE_IDLE = "assets/images/charactor/ro2t/idle.png"
    SPRITE_ATTACK = "assets/images/charactor/ro2t/attack.png"
    SPRITE_JUMP = "assets/images/charactor/ro2t/jump.png"
    SPRITE_SKILL = "assets/images/charactor/ro2t/skill.png"

    DOMAIN_BG_PATH = "assets/images/charactor/ro2t/domain_final.png"

    AURA_KIND = "rings"
    AURA_COLORS = ((80, 235, 190), (170, 255, 240))

    PROJECTILE_KIND = "logic"
    ZONE_KIND = "grid"
    SPECIAL_KIND = "logic"

    BASIC_LABEL = "DATA SHOT"
    ZONE_LABEL = "SCAN FIELD"
    DASH_LABEL = "TRACE"
    SPECIAL_LABEL = "SYSTEM CHECK"

    def __init__(self, x, y, name="RO2T", player_id=2, max_hp=300):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)

        self.color = (38, 142, 132)
        self.trim_color = (8, 60, 64)
        self.glow_color = (80, 235, 190)

        self.projectile_color = (75, 235, 190)
        self.projectile_core = (170, 240, 255)

        self.zone_color = (70, 210, 210)

        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = self.glow_color

        self.profile_key = "RO2T"

        self.WALK_SPEED = 1.9

    def _spawn_concept_projectiles(
        self,
        count=2,
        spread=0.32,
        damage=None,
        speed=None,
        size=None,
    ):
        damage = 12 if damage is None else damage
        speed = 4.6 if speed is None else speed
        size = 16 if size is None else size

        for i, offset in enumerate((-0.18, 0.18)):
            self._spawn_projectile(
                speed=speed,
                damage=damage,
                delay=i * 6,
                angle_offset=offset,
                orbit=40,
                size=size,
                kind="logic",
            )

    def _spawn_concept_zones(self):
        self._spawn_zone_on_target(
            120,
            90,
            warn=36,
            active=18,
            damage=13,
            kind="grid",
        )

    def _spawn_concept_special(self, psys=None):
        for ox in (-100, 100):
            self._spawn_zone_on_target(
                110,
                90,
                warn=28,
                active=18,
                damage=12,
                offset_x=ox,
                kind="grid",
            )

        self._spawn_projectile(
            speed=4.2,
            damage=18,
            orbit=52,
            size=22,
            kind="logic",
        )
