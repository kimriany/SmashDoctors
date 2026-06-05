"""Doctor Purple — 스킬 특화, 피로도 관리가 핵심."""
from entities.player import Player
from systems.skill import Skill


class DoctorPurple(Player):
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
    DISPLAY_NAME  = "Dr. Purple"
    DESCRIPTION   = "스킬 쿨다운 짧고 피로도 소모 적음.\n스킬 콤보로 승부."
    PREVIEW_COLOR = (155, 60, 220)
    SKILL_NAME    = "Void Pulse"

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color       = self.BODY_COLOR
        self.trim_color  = self.TRIM_COLOR
        self.glow_color  = self.GLOW_COLOR
        self.dark_color  = self.DARK_COLOR
        self.max_jumps   = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG
        self.skills["skill_1"] = Skill(
            name=self.SKILL_NAME, damage=20,
            fatigue_cost=20, cooldown=60)

    def get_char_name(self): return "Dr. Purple"
