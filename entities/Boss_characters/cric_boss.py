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
        self.pattern_cooldown = 90
        self._retreat_dir = 1
        self._retreat_rethink = 0

    def configure_profile(self, profile):
        # CricBoss is already a concrete boss, so keep its own art and pattern.
        return

    def _choose_next_pattern(self):
        self.cast_action = "rna_cycle"
        self.cast_label = "RNA SEQUENCE"
        self.cast_timer = 30
        self.cast_total = 30
        self.pattern_cooldown = 300

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
        elif action == "rna_cycle":
            self._spawn_rna_cycle()

    def _move_toward_combat_range(self, platforms):
        if self.target is None:
            return super()._move_toward_combat_range(platforms)
        dx = self.rect.centerx - self.target.rect.centerx
        if self._retreat_rethink <= 0:
            self._retreat_dir = 1 if dx >= 0 else -1
            self._retreat_rethink = 36
        else:
            self._retreat_rethink -= 1

        floor = self._platform_under_x(self.rect.centerx)
        if floor and self.on_ground:
            if self.rect.left <= floor.left + 36:
                self._retreat_dir = 1
                self._retreat_rethink = 24
            elif self.rect.right >= floor.right - 36:
                self._retreat_dir = -1
                self._retreat_rethink = 24

        desired = self._retreat_dir
        self.vel.x += (desired * (self.WALK_SPEED + 0.45) - self.vel.x) * 0.038
        self.facing = -desired
        if self.on_ground and abs(dx) < 240 and random.random() < 0.015:
            self.vel.y = -10.5

    def _spawn_rna_cycle(self):
        for i in range(5):
            self._schedule(i * 60, self._spawn_rna_missile)
        self._schedule(300, self._spawn_rna_prison)

    def _spawn_rna_missile(self):
        if not self.target:
            return
        self._aimed_projectile_from(
            self.rect.centerx,
            self.rect.centery - 26,
            speed=6.2,
            damage=14,
            size=18,
            kind="dna",
            life=150,
        )

    def _spawn_rna_prison(self):
        if not self.target:
            return
        self._spawn_zone_on_target(
            210,
            190,
            warn=34,
            active=76,
            damage=18,
            kind="snare",
        )
        if self.zones:
            self.zones[-1].update({
                "slow": True,
                "slow_x": 0.35,
                "slow_y": 0.55,
                "tick_interval": 32,
            })

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
