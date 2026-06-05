"""Doctor Red — 강한 한방, 무겁고 느림."""
from entities.player import Player
from systems.skill import Skill


class Einstein(Player):
    WEIGHT     = 112
    KB_GROWTH  = 72
    BASE_KB    = 38
    WALK_SPEED = 5.8
    JUMP_POWER = -14.5
    MAX_JUMPS  = 2
    ATTACK_DMG = 16
    ATK_FRAMES = 24
    ATK_CD     = 40
    HIT_START  = 5
    HIT_END    = 18

    BODY_COLOR    = (225, 55, 55)
    TRIM_COLOR    = (145, 20, 20)
    GLOW_COLOR    = (255, 130, 110)
    DARK_COLOR    = (110, 15, 15)
    DISPLAY_NAME  = "Dr. Red"
    DESCRIPTION   = "강력한 한방을 자랑하는 레드 닥터.\n무겁고 강하다."
    PREVIEW_COLOR = (225, 55, 55)
    SKILL_NAME    = "Power Smash"

    SPRITE_PATH = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Nobel/jump.png"  # 없으면 IDLE 사용
    SPRITE_ATTACK = "assets/images/charactor/Nobel/attack.png"  # 없으면 IDLE 사용
    SPRITE_SKILL = "assets/images/charactor/Nobel/skill.png"  # 없으면 IDLE 사용

    # 크기 조절 변수들
    SPRITE_SCALE = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    #스킬 이펙트 위치 조정
    SKILL_BEAM_OFFSET_X = 0
    SKILL_BEAM_OFFSET_Y = 0
    SKILL_AURA_OFFSET_X = 0
    SKILL_AURA_OFFSET_Y = 0

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color       = self.BODY_COLOR
        self.trim_color  = self.TRIM_COLOR
        self.glow_color  = self.GLOW_COLOR
        self.dark_color  = self.DARK_COLOR
        self.max_jumps   = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG
        self.skills["skill_1"] = Skill(
            name=self.SKILL_NAME, damage=38,
            fatigue_cost=40, cooldown=120)

    def get_char_name(self): return "Dr. Red"


