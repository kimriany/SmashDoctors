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
