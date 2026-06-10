"""
Einstein — 무겁고 강력, 한방 특화

스킬 구성:
  Q / ;  basic   — Gravity Beam    (BeamSkill)      전방 중력 빔, 강한 데미지
  E / '  cc      — Black Hole      (SummonZoneSkill) 전방 구역에 블랙홀 소환, 끌어당김
  R / /  enhance — Mass Boost      (EnhanceSkill)   무게 + 공격력 강화, 넉백 저항
"""
from entities.player import Player
from systems.skill import BeamSkill, SummonZoneSkill, EnhanceSkill, DomainUltimateSkill
import pygame


class GravityBeam(BeamSkill):
    DISPLAY_NAME = "Gravity Beam"
    DESCRIPTION  = "Fire a heavy gravity beam.\nHigh damage, slow startup."
    BEAM_LENGTH  = 300
    BEAM_WIDTH   = 32
    BEAM_COLOR   = (255, 130, 110)
    BEAM_GLOW    = (255, 200, 180)
    COOLDOWN_SEC = 6.0

    def __init__(self):
        super().__init__("Gravity Beam", damage=35,
                         cooldown=360, duration=28)


class BlackHole(SummonZoneSkill):
    DISPLAY_NAME = "Black Hole"
    DESCRIPTION  = "Summon a black hole that pulls the enemy in."
    WARN_FRAMES  = 45
    ZONE_W       = 130
    ZONE_H       = 130
    ZONE_COLOR   = (225, 55, 55)
    ZONE_GLOW    = (255, 100, 80)
    COOLDOWN_SEC = 9.0

    def __init__(self):
        super().__init__("Black Hole", damage=20,
                          cooldown=540, duration=100)

    def on_update(self, owner, event_bus=None, psys=None):
        # 경고 이후 — 매 프레임 상대를 끌어당김
        if self.timer <= self.duration - self.WARN_FRAMES:
            zx = getattr(self, '_zone_x', owner.rect.centerx)
            zy = getattr(self, '_zone_y', owner.rect.bottom)
            # owner._skill_target이 있으면 당기기 (game.py에서 설정)
            target = getattr(owner, '_skill_target', None)
            if target and not target.dead:
                dx = zx - target.rect.centerx
                dy = zy - 60 - target.rect.centery
                dist = max(1, (dx**2 + dy**2) ** 0.5)
                pull = 2.5
                target.vel.x += (dx / dist) * pull
                target.vel.y += (dy / dist) * pull * 0.5


class MassBoost(EnhanceSkill):
    DISPLAY_NAME  = "Mass Boost"
    DESCRIPTION   = "Increase weight and attack power.\nResist knockback for 5s."
    SPEED_MULT    = 0.85   # 살짝 느려짐
    DMG_BONUS     = 8
    ENHANCE_COLOR = (255, 130, 110)
    COOLDOWN_SEC  = 14.0

    def __init__(self):
        super().__init__("Mass Boost", damage=0,
                          cooldown=840, duration=300)

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        owner._kb_resist = 0.5   # 넉백 50% 감소

    def on_end(self, owner):
        super().on_end(owner)
        if hasattr(owner, '_kb_resist'):
            del owner._kb_resist

class EinsteinDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Einstein Domain"
    DESCRIPTION = "Open Einstein' special domain."

    # 네가 원하는 이미지 경로로 바꾸면 됨
    DOMAIN_BG_PATH = "assets/images/Einstein_domain.jpeg"

    # 배경 전환 경계 파티클 색상
    DOMAIN_PARTICLE_COLOR = (110, 185, 255)

    # 이 횟수만큼 맞으면 영역 해제
    BREAK_HITS = 5

    # 카메라 워킹 설정
    # 작을수록 빠름
    CUTSCENE_FRAMES = 30
    CUTSCENE_ZOOM = 1.48

    # 배경 전환 속도
    # 클수록 빠름
    TRANSITION_SPEED = 0.055

    # 배경 전환 중에도 gameplay freeze 유지
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(
            name="Einstein Domain",
            damage=0,
            duration=999999,
        )


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
    DISPLAY_NAME  = "Einstein"
    DESCRIPTION   = "Heavy hitter with massive knockback.\nSlow but devastating."
    PREVIEW_COLOR = (225, 55, 55)
    SKILL_NAME    = "Gravity Beam"

    SPRITE_PATH   = "assets/images/charactor/Einstein/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/Einstein/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/Einstein/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Einstein/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/Einstein/skill.png"

    SPRITE_SCALE    = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic":   ("Gravity Beam", "BeamSkill",      35, 40, 6.0),
        "cc":      ("Black Hole",   "SummonZoneSkill", 20, 45, 9.0),
        "enhance": ("Mass Boost",   "EnhanceSkill",     0, 40, 14.0),
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
        self.skills["skill_Q"] = GravityBeam()   # Q / ;
        self.skills["skill_E"] = BlackHole()      # E / '
        self.skills["skill_R"] = EinsteinDomain()
    def get_char_name(self): return "Einstein"
