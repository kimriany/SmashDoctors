"""Doctor Blue — 기본 캐릭터 (빠름, 가벼움)."""
from entities.player import Player
from systems.skill import Skill


class DoctorBlue(Player):
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
    DISPLAY_NAME  = "Dr. Blue"
    DESCRIPTION   = "빠르고 기민한 블루 닥터.\n연속 공격에 특화."
    PREVIEW_COLOR = (55, 130, 230)
    SKILL_NAME    = "Lightning Dash"

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color       = self.BODY_COLOR
        self.trim_color  = self.TRIM_COLOR
        self.glow_color  = self.GLOW_COLOR
        self.dark_color  = self.DARK_COLOR
        self.vel.x       = 0
        self.max_jumps   = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG
        self.skills["skill_1"] = Skill(
            name=self.SKILL_NAME, damage=22,
            fatigue_cost=28, cooldown=85)

    def get_char_name(self): return "Dr. Blue"


