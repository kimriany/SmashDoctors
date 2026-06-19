import math
import random

from entities.Boss_characters.sprite_boss_base import ConceptBoss


class CurieBoss(ConceptBoss):
    DISPLAY_NAME = "Curie Boss"
    STORY_DOMAIN_RULES = {
        "final_lock": True,
        "boss_phase2_hp_ratio": 0.65,
        "boss_domain_start_hp_ratio": 0.35,
        "boss_domain_hp": 100.0,
        "counter_domain_delay_frames": 8 * 60,
        "double_domain_break_delay_frames": 12 * 60,
        "double_domain_break_boss_hp_ratio": 0.15,
        "finisher_ready_on_break": True,
    }
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
        self._curie_mode = "floor"
        self._curie_timer = 600
        self._curie_dir = 1
        self.pattern_cooldown = 999999

    def _choose_next_pattern(self):
        self.pattern_cooldown = 999999

    def _move_toward_combat_range(self, platforms):
        floor = self._main_platform()
        self._curie_timer -= 1
        if self._curie_timer <= 0:
            self._curie_mode = "x" if self._curie_mode == "floor" else "floor"
            self._curie_timer = 260 if self._curie_mode == "x" else 600

        if self._curie_mode == "floor":
            if floor:
                self.rect.bottom = floor.top
                if self.rect.left <= floor.left + 20:
                    self._curie_dir = 1
                elif self.rect.right >= floor.right - 20:
                    self._curie_dir = -1
            self.vel.x += (self._curie_dir * 4.2 - self.vel.x) * 0.08
            self.facing = self._curie_dir
            if self._curie_timer % 18 == 0:
                self._spawn_zone_at(self.rect.centerx, self.rect.bottom + 4, 96, 150,
                                    warn=60, active=18, damage=17, kind="radiation")
        else:
            main = floor or self._platform_under_x(self.rect.centerx)
            if main:
                t = 1.0 - self._curie_timer / 260
                left = main.left + 130
                right = main.right - 130
                top = main.top - 230
                bottom = main.top - 30
                if t < 0.5:
                    k = t / 0.5
                    self.rect.centerx = int(left + (right - left) * k)
                    self.rect.centery = int(bottom + (top - bottom) * k)
                else:
                    k = (t - 0.5) / 0.5
                    self.rect.centerx = int(right + (left - right) * k)
                    self.rect.centery = int(bottom + (top - bottom) * k)
                self.vel.x = 0
                self.vel.y = 0
            if self._curie_timer % 16 == 0:
                self._spawn_curie_x_mark()

    def _spawn_curie_x_mark(self):
        if not self.target:
            return
        cx = self.target.rect.centerx
        bottom = self.target.rect.bottom
        for ox in (-72, 72):
            self._spawn_zone_at(cx + ox, bottom, 92, 190, warn=22, active=18,
                                damage=14, kind="radiation")

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
