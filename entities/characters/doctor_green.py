"""Doctor Green — 점프 특화, 공중전 강함."""
from entities.player import Player
from systems.skill import Skill


class DoctorGreen(Player):
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
    DISPLAY_NAME  = "Dr. Green"
    DESCRIPTION   = "3단 점프로 공중을 지배.\n경쾌하지만 한방이 약하다."
    PREVIEW_COLOR = (55, 200, 90)
    SKILL_NAME    = "Aerial Spike"

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color       = self.BODY_COLOR
        self.trim_color  = self.TRIM_COLOR
        self.glow_color  = self.GLOW_COLOR
        self.dark_color  = self.DARK_COLOR
        self.max_jumps   = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG
        self.skills["skill_1"] = Skill(
            name=self.SKILL_NAME, damage=26,
            fatigue_cost=30, cooldown=90)

    def get_char_name(self): return "Dr. Green"


