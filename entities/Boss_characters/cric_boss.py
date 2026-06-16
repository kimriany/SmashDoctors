import math
import random

from entities.Boss_characters.sprite_boss_base import SpriteBoss, first_existing


class CricBoss(SpriteBoss):
    DISPLAY_NAME = "Crick Boss"

    SPRITE_IDLE = "assets/images/charactor/cric/IDL.png"
    SPRITE_ATTACK = "assets/images/charactor/cric/attack.png"
    SPRITE_JUMP = "assets/images/charactor/cric/jump.png"
    DOMAIN_BG_PATH = first_existing([
        "assets/images/charactor/cric/cric_domain.png",
        "assets/images/story/Phylab.png",
    ])
    SPRITE_SCALE = 1.13
    SPRITE_SCALE_X = 1.04
    SPRITE_OFFSET_Y = 5
    AURA_KIND = "helix"
    AURA_COLORS = ((115, 225, 255), (255, 230, 120))

    DNA_COLORS = (
        (115, 225, 255),
        (120, 255, 180),
        (255, 230, 120),
        (210, 145, 255),
    )

    def __init__(self, x, y, name="크릭", player_id=2, max_hp=1350):
        super().__init__(x, y, name=name, player_id=player_id, max_hp=max_hp)

        self.rect.w = 70
        self.rect.h = 96
        self.color = (82, 140, 180)
        self.trim_color = (25, 58, 100)
        self.glow_color = (120, 230, 255)
        self.dark_color = (8, 24, 48)
        self.projectile_color = (115, 225, 255)
        self.projectile_core = (255, 245, 160)
        self.zone_color = (86, 200, 245)
        self.domain_bg_path = self.DOMAIN_BG_PATH
        self.domain_particle_color = (120, 230, 255)
        self.profile_key = "crick"
        self.special_pattern = "cric_double_helix"
        self.special_label = "DOUBLE HELIX"

        self.WALK_SPEED = 2.05
        self.boss_domain_max_hp = 360.0
        self.boss_domain_hp = self.boss_domain_max_hp

    def configure_profile(self, profile):
        # CricBoss is already a concrete boss, so keep its own art and pattern.
        return

    def _choose_next_pattern(self):
        if self.phase <= 1:
            options = ["helix_orbs", "base_pair_zone", "replication_dash"]
        elif self.phase == 2:
            options = ["helix_orbs", "base_pair_zone", "replication_dash", "codon_rain"]
        elif self.phase == 3:
            options = ["helix_orbs", "codon_rain", "double_helix", "replication_dash"]
        else:
            options = ["double_helix", "codon_rain", "helix_orbs", "replication_dash"]

        choice = random.choice(options)
        cast_frames = {
            "helix_orbs": 40,
            "base_pair_zone": 42,
            "replication_dash": 28,
            "codon_rain": 52,
            "double_helix": 62,
        }[choice]
        if self.domain_active:
            cast_frames = max(18, int(cast_frames * 0.75))

        labels = {
            "helix_orbs": "HELIX ORBS",
            "base_pair_zone": "BASE PAIR",
            "replication_dash": "REPLICATION",
            "codon_rain": "CODON RAIN",
            "double_helix": "DOUBLE HELIX",
        }
        self.cast_action = choice
        self.cast_label = labels[choice]
        self.cast_timer = cast_frames
        self.cast_total = cast_frames
        self.pattern_cooldown = 48 + random.randint(0, 28)

    def _resolve_cast(self, event_bus, psys):
        action = self.cast_action
        self.cast_action = None
        self.cast_label = ""

        if action == "helix_orbs":
            self._spawn_helix_orbs(count=2 if self.phase < 3 else 3)
        elif action == "base_pair_zone":
            self._spawn_base_pair_zones()
        elif action == "replication_dash":
            self._spawn_afterimage_clones(psys)
            self.dash_timer = 22
            self.dash_has_hit = False
            self.vel.x = self.facing * (9.6 if self.domain_active else 8.4)
        elif action == "codon_rain":
            self._spawn_codon_rain()
        elif action == "double_helix":
            self._spawn_double_helix()

    def _spawn_helix_orbs(self, count=2):
        offsets = [-0.28, 0.28] if count == 2 else [-0.42, 0.0, 0.42]
        for i, offset in enumerate(offsets):
            self._spawn_projectile(
                speed=5.6,
                damage=18,
                delay=i * 5,
                angle_offset=offset,
                orbit=52 + i * 8,
                size=21,
                kind="dna",
            )

    def _spawn_base_pair_zones(self):
        for i, ox in enumerate((-110, 0, 110)):
            self._spawn_zone_on_target(
                96,
                88,
                warn=34 + i * 8,
                active=18,
                damage=17,
                offset_x=ox,
                kind="base_pair",
            )

    def _spawn_codon_rain(self):
        for i in range(6 if self.domain_active else 4):
            self._spawn_zone_on_target(
                86,
                150,
                warn=26 + i * 8,
                active=14,
                damage=15,
                offset_x=random.randint(-220, 220),
                kind="codon",
            )

    def _spawn_double_helix(self):
        for i in range(6):
            angle = -0.72 + i * 0.288
            self._spawn_projectile(
                speed=4.8 + i * 0.12,
                damage=15,
                delay=i * 4,
                angle_offset=angle,
                orbit=46 + i * 5,
                size=17 + (i % 2) * 4,
                kind="dna",
            )
        for i in range(4):
            self._spawn_zone_on_target(
                112,
                86,
                warn=38 + i * 10,
                active=16,
                damage=16,
                offset_x=(i - 1.5) * 92,
                kind="base_pair",
            )

    def _spawn_afterimage_clones(self, psys=None):
        for i in range(3):
            ghost = self.rect.copy()
            ghost.x -= self.facing * (38 + i * 26)
            self.afterimages.append({"rect": ghost, "life": 24 + i * 4})
        if psys:
            psys.spawn(self.rect.centerx, self.rect.centery, self.glow_color, count=30, speed=6, gravity=-0.03, life=32, r=5, glow=True)

    def _zone_draw_color(self, zdata):
        kind = zdata.get("kind", "zone")
        if kind == "base_pair":
            return (115, 225, 255)
        if kind == "codon":
            return (150, 255, 170)
        return super()._zone_draw_color(zdata)
