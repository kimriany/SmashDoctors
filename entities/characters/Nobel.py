"""
Nobel — 폭발물과 발파 구역으로 공간을 통제하는 캐릭터.

일반 스킬:
  Q / ;  Bomb Toss        — ProjectileSkill, 전방으로 폭탄 투척
  E / '  Remote Blast     — SummonZoneSkill, 전방 일정 영역 폭파
  R / /  Nobel Domain     — nobel_domain.png 영역 전개

영역 전개 중 강화 스킬:
  Q / ;  Nitroglycerin Bomb — 더 크고 빠른 폭탄
  E / '  Chain Detonation   — 넓은 다단 폭파 구역
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


class BombToss(_NormalOnlyMixin, ProjectileSkill):
    DISPLAY_NAME = "Bomb Toss"
    DESCRIPTION = "Throw a bomb forward.\nA simple projectile with strong knockback."
    PROJ_SPEED = 9.5
    PROJ_SIZE = 16
    PROJ_COLOR = (245, 180, 60)
    PROJ_GLOW = (255, 230, 130)
    ARTIFACT_PATH = "assets/images/charactor/Nobel/nobel_bomb.png"
    ICON_PATH = "assets/images/charactor/Nobel/nobel_bomb.png"
    COOLDOWN_SEC = 4.5

    def __init__(self):
        super().__init__("Bomb Toss", damage=20, cooldown=270, duration=82)
        self.charge_value = 0.9

    def on_start(self, owner, event_bus=None, psys=None):
        self._px = float(owner.rect.centerx + owner.facing * 28)
        self._py = float(owner.rect.centery - 10)
        self._vx = self.PROJ_SPEED * owner.facing
        self._vy = -3.8
        self._alive = True
        if psys:
            psys.spawn(owner.rect.centerx, owner.rect.centery, self.PROJ_COLOR,
                       count=5, speed=3, life=14, r=3)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive:
            return
        self._px += self._vx
        self._py += self._vy
        self._vy += 0.18
        if psys and self.timer % 5 == 0:
            psys.spawn(int(self._px), int(self._py), (80, 70, 60),
                       count=1, speed=1.5, life=12, r=3)
        if abs(self._px - owner.rect.centerx) > 780 or self._py > owner.rect.bottom + 360:
            self._alive = False

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._alive = False
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.PROJ_GLOW,
                       count=18, speed=7, life=24, r=5)
        super().on_hit(owner, target, event_bus, psys, fsys)


class RemoteBlast(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Remote Blast"
    DESCRIPTION = "Plant a danger zone ahead.\nIt explodes after a short warning."
    WARN_FRAMES = 34
    ZONE_W = 150
    ZONE_H = 105
    ZONE_COLOR = (240, 120, 45)
    ZONE_GLOW = (255, 210, 90)
    EFFECT_PATH = "assets/images/charactor/Nobel/nobel_explosion.png"
    ICON_PATH = "assets/images/charactor/Nobel/nobel_explosion.png"
    COOLDOWN_SEC = 8.0

    def __init__(self):
        super().__init__("Remote Blast", damage=24, cooldown=480, duration=86)
        self.charge_value = 1.25

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            dx = target.rect.centerx - owner.rect.centerx
            if abs(dx) <= 360:
                self._zone_x = target.rect.centerx
            else:
                self._zone_x = owner.rect.centerx + owner.facing * 230
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 230
        self._zone_y = owner.rect.bottom

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        if psys:
            zx = getattr(self, "_zone_x", target.rect.centerx)
            zy = getattr(self, "_zone_y", target.rect.bottom) - self.ZONE_H // 2
            psys.spawn(zx, zy, self.ZONE_GLOW, count=24, speed=8, life=26, r=6)
        target.vel.y -= 6
        super().on_hit(owner, target, event_bus, psys, fsys)


class NobelDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Nobel Domain"
    DESCRIPTION = "Open Nobel's explosive domain.\nBomb skills become stronger."
    DOMAIN_BG_PATH = "assets/images/charactor/Nobel/nobel_domain.png"
    DOMAIN_PARTICLE_COLOR = (255, 190, 70)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 32
    CUTSCENE_ZOOM = 1.42
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Nobel Domain", damage=0, duration=999999)


class NitroglycerinBomb(_DomainOnlyMixin, BombToss):
    DISPLAY_NAME = "Nitroglycerin Bomb"
    DESCRIPTION = "Domain skill — larger, faster bomb.\nHigh damage and finisher charge."
    PROJ_SPEED = 13.5
    PROJ_SIZE = 24
    PROJ_COLOR = (255, 95, 35)
    PROJ_GLOW = (255, 230, 100)
    ARTIFACT_PATH = "assets/images/charactor/Nobel/nobel_bomb.png"
    ICON_PATH = "assets/images/charactor/Nobel/nobel_bomb.png"
    COOLDOWN_SEC = 3.0

    def __init__(self):
        ProjectileSkill.__init__(
            self,
            "Nitroglycerin Bomb",
            damage=38,
            cooldown=180,
            duration=74,
        )
        self.charge_value = 0.0
        self.finisher_charge_value = 1.8

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        self._vy = -2.4
        if psys:
            for _ in range(12):
                psys.spawn(owner.rect.centerx + owner.facing * 28,
                           owner.rect.centery - 10,
                           random.choice([(255, 90, 30), (255, 210, 80)]),
                           count=1, speed=random.uniform(3, 7),
                           life=random.randint(12, 22), r=random.randint(3, 6))

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x += owner.facing * 14
        target.vel.y -= 5
        super().on_hit(owner, target, event_bus, psys, fsys)


class ChainDetonation(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Chain Detonation"
    DESCRIPTION = "Domain skill — wide blast field.\nRepeated detonations pull and launch."
    WARN_FRAMES = 14
    ZONE_W = 250
    ZONE_H = 145
    ZONE_COLOR = (255, 80, 25)
    ZONE_GLOW = (255, 235, 120)
    EFFECT_PATH = "assets/images/charactor/Nobel/nobel_explosion.png"
    ICON_PATH = "assets/images/charactor/Nobel/nobel_explosion.png"
    COOLDOWN_SEC = 6.5
    MULTI_HIT_INTERVAL = 28

    def __init__(self):
        super().__init__("Chain Detonation", damage=16, cooldown=390, duration=132)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.6
        self._hit_timer = 0

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        self._zone_x = owner.rect.centerx + owner.facing * 170
        self._zone_y = owner.rect.bottom
        self._hit_timer = 0

    def on_update(self, owner, event_bus=None, psys=None):
        if self.timer <= self.duration - self.WARN_FRAMES:
            self._hit_timer += 1
            if self._hit_timer >= self.MULTI_HIT_INTERVAL:
                self._hit_timer = 0
                self.has_hit = False

            target = getattr(owner, "_skill_target", None)
            if target and not target.dead:
                zx = getattr(self, "_zone_x", owner.rect.centerx)
                dx = zx - target.rect.centerx
                if abs(dx) < self.ZONE_W:
                    target.vel.x += math.copysign(0.9, dx)

            if psys and self.timer % 8 == 0:
                zx = getattr(self, "_zone_x", owner.rect.centerx)
                zy = getattr(self, "_zone_y", owner.rect.bottom)
                psys.spawn(
                    zx + random.randint(-self.ZONE_W // 2, self.ZONE_W // 2),
                    zy - random.randint(15, self.ZONE_H),
                    random.choice([(255, 90, 30), (255, 190, 70), (90, 70, 45)]),
                    count=2, speed=random.uniform(2, 5),
                    life=random.randint(12, 22), r=random.randint(3, 6)
                )

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.y -= 8
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, self.ZONE_GLOW,
                       count=20, speed=7, life=22, r=5)
        super().on_hit(owner, target, event_bus, psys, fsys)


class Nobel(Player):
    WEIGHT = 88
    KB_GROWTH = 90
    BASE_KB = 26
    WALK_SPEED = 6.0
    JUMP_POWER = -17.5
    MAX_JUMPS = 3
    ATTACK_DMG = 10
    ATK_FRAMES = 18
    ATK_CD = 28
    HIT_START = 3
    HIT_END = 14

    BODY_COLOR = (55, 200, 90)
    TRIM_COLOR = (20, 120, 50)
    GLOW_COLOR = (130, 255, 160)
    DARK_COLOR = (15, 80, 35)
    DISPLAY_NAME = "Nobel"
    DESCRIPTION = (
        "Explosive zoner with triple jump.\n"
        "Domain upgrades bomb skills."
    )
    PREVIEW_COLOR = (55, 200, 90)
    SKILL_NAME = "Bomb Toss"

    SPRITE_PATH = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Nobel/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Nobel/attack.png"
    SPRITE_SKILL = "assets/images/charactor/Nobel/skill.png"

    SPRITE_SCALE = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Bomb Toss", "ProjectileSkill", 20, 25, 4.5),
        "cc": ("Remote Blast", "SummonZoneSkill", 24, 36, 8.0),
        "enhance": ("Nobel Domain", "DomainUltimateSkill", 0, 0, 0.0),
    }

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR
        self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR
        self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"] = BombToss()
        self.skills["skill_E"] = RemoteBlast()
        self.skills["skill_R"] = NobelDomain()
        self.skills["skill_Q_domain"] = NitroglycerinBomb()
        self.skills["skill_E_domain"] = ChainDetonation()

    def use_skill(self, skill_key: str, event_bus=None, psys=None) -> bool:
        domain_key = skill_key + "_domain"
        if domain_key in self.skills:
            domain_skill = self.skills[domain_key]
            if domain_skill.can_use(self):
                domain_skill.use(self, event_bus, psys)
                self.active_skill = domain_skill
                return True

        skill = self.skills.get(skill_key)
        if skill and skill.can_use(self):
            skill.use(self, event_bus, psys)
            self.active_skill = skill
            return True

        return False

    def get_char_name(self):
        return "Nobel"
