"""
Nobel — 3단 점프, 공중전 특화

스킬 구성:
  Q / ;  basic   — Aerial Spike    (ProjectileSkill) 공중에서 아래로 투사체 발사
  E / '  cc      — Wind Barrier    (SummonZoneSkill) 발 아래 바람 구역 소환
  R / /  enhance — Feather Fall    (EnhanceSkill)    체공시간 + 공중 기동력 강화
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, EnhanceSkill
import pygame


class AerialSpike(ProjectileSkill):
    DISPLAY_NAME = "Aerial Spike"
    DESCRIPTION  = "Launch a fast orb forward.\nBest used in mid-air."
    PROJ_SPEED   = 12.0
    PROJ_SIZE    = 14
    PROJ_COLOR   = (130, 255, 160)
    PROJ_GLOW    = (200, 255, 220)
    COOLDOWN_SEC = 4.0

    def __init__(self):
        super().__init__("Aerial Spike", damage=18,
                          cooldown=240, duration=60)


class WindBarrier(SummonZoneSkill):
    DISPLAY_NAME = "Wind Barrier"
    DESCRIPTION  = "Summon a wind zone that launches enemies upward."
    WARN_FRAMES  = 35
    ZONE_W       = 100
    ZONE_H       = 90
    ZONE_COLOR   = (130, 255, 160)
    ZONE_GLOW    = (200, 255, 210)
    COOLDOWN_SEC = 7.0

    def __init__(self):
        super().__init__("Wind Barrier", damage=14,
                          cooldown=420, duration=80)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 위로 날려보내는 CC 추가
        target.vel.y = -16
        super().on_hit(owner, target, event_bus, psys, fsys)


class FeatherFall(EnhanceSkill):
    DISPLAY_NAME  = "Feather Fall"
    DESCRIPTION   = "Slow fall speed and gain extra air mobility."
    SPEED_MULT    = 1.3
    DMG_BONUS     = 0
    ENHANCE_COLOR = (130, 255, 160)
    COOLDOWN_SEC  = 12.0

    def __init__(self):
        super().__init__("Feather Fall", damage=0,
                         cooldown=720, duration=300)

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        # 체공 중 중력 감소
        owner._gravity_override = 0.25

    def on_end(self, owner):
        super().on_end(owner)
        if hasattr(owner, '_gravity_override'):
            del owner._gravity_override


class Nobel(Player):
    WEIGHT     = 88
    KB_GROWTH  = 90
    BASE_KB    = 26
    WALK_SPEED = 6.0
    JUMP_POWER = -17.5
    MAX_JUMPS  = 3
    ATTACK_DMG = 10
    ATK_FRAMES = 18
    ATK_CD     = 28
    HIT_START  = 3
    HIT_END    = 14

    BODY_COLOR    = (55, 200, 90)
    TRIM_COLOR    = (20, 120, 50)
    GLOW_COLOR    = (130, 255, 160)
    DARK_COLOR    = (15,  80, 35)
    DISPLAY_NAME  = "Nobel"
    DESCRIPTION   = "Triple jump, air combat master.\nLight but deals less damage."
    PREVIEW_COLOR = (55, 200, 90)
    SKILL_NAME    = "Aerial Spike"

    SPRITE_PATH   = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/Nobel/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Nobel/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/Nobel/skill.png"

    SPRITE_SCALE    = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic":   ("Aerial Spike",  "ProjectileSkill", 18, 22, 4.0),
        "cc":      ("Wind Barrier",  "SummonZoneSkill", 14, 30, 7.0),
        "enhance": ("Feather Fall",  "EnhanceSkill",     0, 25, 12.0),
    }

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color         = self.BODY_COLOR
        self.trim_color    = self.TRIM_COLOR
        self.glow_color    = self.GLOW_COLOR
        self.dark_color    = self.DARK_COLOR
        self.max_jumps     = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"] = AerialSpike()   # Q / ;
        self.skills["skill_E"] = WindBarrier()    # E / '

    def get_char_name(self): return "Nobel"
