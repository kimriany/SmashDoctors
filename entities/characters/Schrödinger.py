"""
Schrödinger — 스킬 콤보 특화, 낮은 쿨타임

스킬 구성:
  Q / ;  basic   — Void Pulse      (BeamSkill)      짧고 빠른 보라 빔
  E / '  cc      — Cat's Paradox   (TeleportSkill)  상대 뒤로 순간이동
  R / /  enhance — Quantum State   (EnhanceSkill)   스킬 쿨타임 단축 + 피로도 회복
"""
from entities.player import Player
from systems.skill import BeamSkill, TeleportSkill, EnhanceSkill
import pygame


class VoidPulse(BeamSkill):
    DISPLAY_NAME = "Void Pulse"
    DESCRIPTION  = "Short-range void burst.\nLow cooldown, spammable."
    BEAM_LENGTH  = 180
    BEAM_WIDTH   = 18
    BEAM_COLOR   = (210, 130, 255)
    BEAM_GLOW    = (240, 200, 255)
    COOLDOWN_SEC = 2.0

    def __init__(self):
        super().__init__("Void Pulse", damage=16,
                         cooldown=120, duration=18)


class CatsParadox(TeleportSkill):
    DISPLAY_NAME    = "Cat's Paradox"
    DESCRIPTION     = "Teleport behind the enemy.\nStrike before they react."
    TELEPORT_OFFSET = 70
    FLASH_COLOR     = (210, 130, 255)
    COOLDOWN_SEC    = 6.0

    def __init__(self):
        super().__init__("Cat's Paradox", damage=12,
                         cooldown=360, duration=20)

    def on_start(self, owner, event_bus=None, psys=None):
        # active_skill에서 target을 찾아 설정
        super().on_start(owner, event_bus, psys)
        # 순간이동 직후 자동 공격 시작
        owner.start_attack()


class QuantumState(EnhanceSkill):
    DISPLAY_NAME  = "Quantum State"
    DESCRIPTION   = "Reduce all skill cooldowns by 40%."
    SPEED_MULT    = 1.0
    DMG_BONUS     = 2
    ENHANCE_COLOR = (210, 130, 255)
    COOLDOWN_SEC  = 15.0

    def __init__(self):
        super().__init__("Quantum State", damage=0,
                         cooldown=900, duration=360)

    def on_update(self, owner, event_bus=None, psys=None):
        super().on_update(owner, event_bus, psys)
        # 쿨타임 2배속 감소
        for sk in owner.skills.values():
            if sk is not self and sk.current_cooldown > 0:
                sk.current_cooldown = max(0, sk.current_cooldown - 1)


class Schrödinger(Player):
    WEIGHT     = 96
    KB_GROWTH  = 78
    BASE_KB    = 30
    WALK_SPEED = 6.2
    JUMP_POWER = -15.0
    MAX_JUMPS  = 2
    ATTACK_DMG = 9
    ATK_FRAMES = 16
    ATK_CD     = 26
    HIT_START  = 3
    HIT_END    = 13

    BODY_COLOR    = (155, 60, 220)
    TRIM_COLOR    = ( 90, 20, 140)
    GLOW_COLOR    = (210, 130, 255)
    DARK_COLOR    = ( 60, 10, 100)
    DISPLAY_NAME  = "Schrödinger"
    DESCRIPTION   = "Short cooldowns. \nWin with skill combos."
    PREVIEW_COLOR = (155, 60, 220)
    SKILL_NAME    = "Void Pulse"

    SPRITE_PATH   = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/Schrödinger/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Schrödinger/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/Schrödinger/skill.png"

    SPRITE_SCALE    = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic":   ("Void Pulse",    "BeamSkill",      16, 18, 2.0),
        "cc":      ("Cat's Paradox", "TeleportSkill",  12, 30, 6.0),
        "enhance": ("Quantum State", "EnhanceSkill",    0, 20, 15.0),
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
        self.skills["skill_Q"] = VoidPulse()      # Q / ;
        self.skills["skill_E"] = CatsParadox()    # E / '

    def get_char_name(self): return "Schrödinger"
