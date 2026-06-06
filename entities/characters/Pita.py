"""
Pythagoras (Pita) — 빠르고 기민, 연속 공격 특화

스킬 구성:
  Q / ;  basic   — Lightning Dash   (DashSkill)    빠른 전진 대시 + 접촉 데미지
  E / '  cc      — Thunder Bolt     (BeamSkill)    전방 번개 빔
  R / /  enhance — Speed Formula    (EnhanceSkill) 일시적 이동속도 + 공격속도 강화
"""
from entities.player import Player
from systems.skill import BeamSkill, DashSkill, EnhanceSkill


# ── Pita 전용 스킬 클래스 ─────────────────────────────────────

class LightningDash(DashSkill):
    ICON_PATH = "assets/images/Double_domain.jpeg"  # 선택창 아이콘
    DISPLAY_NAME = "Lightning Dash"
    DESCRIPTION  = "Dash forward and deal contact damage."
    DASH_SPEED   = 20.0
    DASH_FRAMES  = 10
    DASH_DAMAGE  = 8
    TRAIL_COLOR  = (110, 185, 255)
    COOLDOWN_SEC = 1.5

    def __init__(self):
        super().__init__("Lightning Dash", damage=8,
                         fatigue_cost=20, cooldown=90, duration=14)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        import pygame
        return pygame.Rect(owner.rect.x - 10, owner.rect.y,
                           owner.rect.w + 20, owner.rect.h)


class ThunderBolt(BeamSkill):
    DISPLAY_NAME = "Thunder Bolt"
    DESCRIPTION  = "Fire a lightning beam that pierces enemies."
    BEAM_LENGTH  = 320
    BEAM_WIDTH   = 22
    BEAM_COLOR   = (140, 210, 255)
    BEAM_GLOW    = (200, 240, 255)
    COOLDOWN_SEC = 5.0

    def __init__(self):
        super().__init__("Thunder Bolt", damage=22,
                         fatigue_cost=28, cooldown=300, duration=22)


class SpeedFormula(EnhanceSkill):
    DISPLAY_NAME  = "Speed Formula"
    DESCRIPTION   = "Boost move speed and attack speed for 4s."
    SPEED_MULT    = 1.7
    DMG_BONUS     = 3
    ENHANCE_COLOR = (110, 185, 255)
    COOLDOWN_SEC  = 10.0

    def __init__(self):
        super().__init__("Speed Formula", damage=0,
                         fatigue_cost=35, cooldown=600, duration=240)


# ── 캐릭터 클래스 ─────────────────────────────────────────────

class Pita(Player):
    WEIGHT     = 92
    KB_GROWTH  = 85
    BASE_KB    = 28
    WALK_SPEED = 7.2
    JUMP_POWER = -16.0
    MAX_JUMPS  = 2
    ATTACK_DMG = 11
    ATK_FRAMES = 18
    ATK_CD     = 30
    HIT_START  = 3
    HIT_END    = 14

    BODY_COLOR    = (55, 130, 230)
    TRIM_COLOR    = (25,  65, 155)
    GLOW_COLOR    = (110, 185, 255)
    DARK_COLOR    = (20,  45, 110)
    DISPLAY_NAME  = "Pythagoras"
    DESCRIPTION   = "Fast and agile.\nSpecializes in combo attacks."
    PREVIEW_COLOR = (55, 130, 230)
    SKILL_NAME    = "Lightning Dash"

    SPRITE_PATH   = "assets/images/charactor/pita/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/pita/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/pita/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/pita/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/pita/skill.png"



    SPRITE_SCALE    = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    # 캐릭터 선택창 스킬 설명 (선택창에서 읽음)
    SKILL_DEFS_META = {
        "basic":   ("Lightning Dash",  "DashSkill",    8,  20, 1.5),
        "cc":      ("Thunder Bolt",    "BeamSkill",   22,  28, 5.0),
        "enhance": ("Speed Formula",   "EnhanceSkill", 0,  35, 10.0),
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
        self.skills["skill_1"] = LightningDash()   # Q / ;
        self.skills["skill_2"] = ThunderBolt()      # E / '
        self.skills["skill_R"] = SpeedFormula()     # R / /

    def get_char_name(self): return "Pythagoras"
