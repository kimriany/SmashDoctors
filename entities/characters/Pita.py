"""
Pythagoras (Pita) — 가렌 스타일, 직각삼각자로 찍고 회전하는 근거리 파이터

일반 스킬:
  Q / ;  Decisive Strike   — 직각삼각자 강타, 발동 중 공격속도 증가
  E / '  Judgement Spin    — 60도 삼각자로 회전하며 연속 타격

영역 전개 중:
  Q / ;  Geometric Verdict — 더 강하고 광역 삼각자 강타 (가렌 궁 느낌)
  E / '  Infinite Spin     — 더 빠르고 오래 지속되는 강화 회전
"""
from entities.player import Player
from systems.skill import Skill, DomainUltimateSkill, BeamSkill, DashSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner): return getattr(owner, "domain_active", False)

class _NormalOnlyMixin:
    def can_activate(self, owner): return not getattr(owner, "domain_active", False)

def _alpha(v): return max(0, min(255, int(v)))


# ── Q: Decisive Strike (가렌 Q — 직각삼각자 찍기 + 공속 증가) ──────────────
class DecisiveStrike(_NormalOnlyMixin, Skill):
    DISPLAY_NAME = "Decisive Strike"
    DESCRIPTION  = "Slam with a right-angle triangle.\nAttack speed increases briefly."
    COOLDOWN_SEC = 3.5

    HIT_FRAME  = 8     # 판정 발생 프레임
    ATK_FRAMES = 22    # 전체 지속

    def __init__(self):
        super().__init__("Decisive Strike", damage=28,
                         cooldown=210, duration=self.ATK_FRAMES)
        self.charge_value     = 1.1
        self._hit_done        = False
        self._speed_boosted   = False
        self._cast_facing     = 1

    def on_start(self, owner, event_bus=None, psys=None):
        self._hit_done      = False
        self._speed_boosted = False
        self._cast_facing   = owner.facing
        # 공격속도 증가 (ATK_CD 절반으로)
        self._orig_atk_cd       = owner.ATK_CD
        owner._atk_cd_override  = max(10, owner.ATK_CD // 2)
        self._speed_boosted = True
        if psys:
            for _ in range(8):
                ang = random.uniform(0, math.pi * 2)
                psys.spawn(owner.rect.centerx + math.cos(ang)*20,
                           owner.rect.centery + math.sin(ang)*20,
                           (110, 185, 255), count=1, speed=4,
                           gravity=0.1, life=14, r=4, glow=True)

    def get_hitbox(self, owner):
        if not self.active: return None
        elapsed = self.duration - self.timer
        if elapsed < self.HIT_FRAME or elapsed > self.HIT_FRAME + 6:
            return None
        w = int(owner.rect.w * 2.2)
        h = int(owner.rect.h * 1.6)
        facing = getattr(self, "_cast_facing", owner.facing)
        x = owner.rect.centerx if facing == 1 else owner.rect.centerx - w
        return pygame.Rect(x, owner.rect.centery - h//2, w, h)

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        # 판정 타이밍에 파티클
        if elapsed == self.HIT_FRAME and psys:
            facing = getattr(self, "_cast_facing", owner.facing)
            cx = owner.rect.centerx + facing * int(owner.rect.w * 0.9)
            cy = owner.rect.centery
            for _ in range(18):
                ang = random.uniform(-math.pi/2, math.pi/2) * facing
                psys.spawn(cx, cy, random.choice([(110,185,255),(255,255,255),(80,140,255)]),
                           count=1, speed=random.uniform(4,10),
                           gravity=0.2, life=random.randint(12,22), r=random.randint(3,6), glow=True)
        # 스킬 종료 시 공속 복구
        if self.timer <= 1 and self._speed_boosted:
            if hasattr(owner, '_atk_cd_override'):
                del owner._atk_cd_override
            self._speed_boosted = False

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        facing = getattr(self, "_cast_facing", owner.facing)
        target.vel.x += facing * 5
        target.vel.y -= 2
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        elapsed = self.duration - self.timer
        t = elapsed / self.duration
        if elapsed < 4 or elapsed > self.HIT_FRAME + 10: return

        swing_t  = min(1.0, elapsed / (self.HIT_FRAME + 4))
        facing   = getattr(self, "_cast_facing", owner.facing)
        angle    = -60 + swing_t * 120   # -60° → +60°
        cx, cy   = dr.centerx + dr.w // 2 * facing, dr.centery + bob
        size     = int(dr.w * 2.2 * z)
        alpha    = _alpha(200 * (1 - abs(swing_t * 2 - 1) * 0.5))

        canvas = size * 4
        sf = pygame.Surface((canvas, canvas), pygame.SRCALPHA)
        sc = canvas // 2
        rad = math.radians(angle)
        # 직각삼각자 세 꼭짓점
        pts = [
            (sc, sc),
            (sc + int(math.cos(rad) * size * 1.8) * facing,
             sc + int(math.sin(rad) * size * 1.8)),
            (sc + int(math.cos(rad + math.pi/2) * size) * facing,
             sc + int(math.sin(rad + math.pi/2) * size)),
        ]
        pygame.draw.polygon(sf, (80, 160, 255, _alpha(alpha * 0.3)), pts)
        pygame.draw.polygon(sf, (220, 245, 255, alpha), pts, max(2, int(3*z)))
        # 직각 표시
        right_pt = pts[0]
        pygame.draw.circle(sf, (255, 255, 255, alpha), right_pt, max(3, int(5*z)))
        screen.blit(sf, (cx - sc, cy - sc))


# ── E: Judgement Spin (가렌 E — 60도 삼각자로 회전하며 다단 딜) ────────────
class JudgementSpin(_NormalOnlyMixin, Skill):
    DISPLAY_NAME = "Judgement Spin"
    DESCRIPTION  = "Spin the triangle ruler, hitting multiple times.\nHits 6 times total."
    COOLDOWN_SEC = 8.0
    SPIN_HITS    = 6
    HIT_INTERVAL = 8   # 몇 프레임마다 히트

    def __init__(self):
        super().__init__("Judgement Spin", damage=14,
                         cooldown=480, duration=52)
        self.charge_value = 1.3
        self._spin_angle  = 0.0
        self._hit_count   = 0
        self._hit_timer   = 0

    def on_start(self, owner, event_bus=None, psys=None):
        self._spin_angle = 0.0
        self._hit_count  = 0
        self._hit_timer  = 0
        if psys:
            psys.spawn(owner.rect.centerx, owner.rect.centery,
                       (110, 185, 255), count=12, speed=5,
                       gravity=-0.05, life=16, r=5, glow=True)

    def get_hitbox(self, owner):
        if not self.active: return None
        r = int(owner.rect.w * 1.6)
        return pygame.Rect(owner.rect.centerx - r, owner.rect.centery - r, r*2, r*2)

    def on_update(self, owner, event_bus=None, psys=None):
        self._spin_angle += 12.0   # 프레임당 회전 속도
        self._hit_timer  += 1
        # 다단 히트 타이밍
        if self._hit_timer >= self.HIT_INTERVAL and self._hit_count < self.SPIN_HITS:
            self._hit_timer  = 0
            self._hit_count += 1
            self.has_hit = False   # 매 히트마다 재발동

        if psys and self.timer % 3 == 0:
            ang = math.radians(self._spin_angle)
            r   = int(owner.rect.w * 1.4)
            psys.spawn(owner.rect.centerx + math.cos(ang) * r,
                       owner.rect.centery + math.sin(ang) * r,
                       (110, 185, 255), count=1, speed=2,
                       gravity=0, life=10, r=4, glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 마지막 히트는 더 강하게
        if self._hit_count >= self.SPIN_HITS:
            target.vel.x += owner.facing * 6
            target.vel.y -= 4
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        t     = self.timer / max(1, self.duration)
        alpha = _alpha(180 + 60 * math.sin(self._spin_angle * 0.1))
        r     = int(dr.w * 1.6 * z)
        cx, cy = dr.centerx, dr.centery + bob

        # 60도 삼각자 회전
        sf  = pygame.Surface((r*2+20, r*2+20), pygame.SRCALPHA)
        sc  = r + 10
        ang = math.radians(self._spin_angle)
        # 삼각자: 두 변은 r 길이, 사이각 60도
        p0 = (sc, sc)
        p1 = (sc + int(math.cos(ang) * r), sc + int(math.sin(ang) * r))
        p2 = (sc + int(math.cos(ang + math.pi/3) * r), sc + int(math.sin(ang + math.pi/3) * r))
        pygame.draw.polygon(sf, (80, 160, 255, _alpha(alpha * 0.25)), [p0, p1, p2])
        pygame.draw.lines(sf, (220, 245, 255, alpha), True, [p0, p1, p2], max(2, int(3*z)))
        # 중심 글로우
        pygame.draw.circle(sf, (110, 185, 255, _alpha(alpha * 0.4)), (sc, sc), r, max(1, int(2*z)))
        screen.blit(sf, (cx - sc, cy - sc))


# ── 영역 궁 ─────────────────────────────────────────────────────────────────
class PitaDomain(DomainUltimateSkill):
    DISPLAY_NAME          = "Pythagorean Domain"
    DESCRIPTION           = "Open Pythagoras' theorem domain."
    DOMAIN_BG_PATH        = "assets/images/charactor/pita/domain.jpeg"
    DOMAIN_PARTICLE_COLOR = (95, 185, 255)
    BREAK_HITS            = 5
    CUTSCENE_FRAMES       = 30
    CUTSCENE_ZOOM         = 1.48
    TRANSITION_SPEED      = 0.055
    FREEZE_DURING_TRANSITION = True
    def __init__(self):
        super().__init__(name="Pythagorean Domain", damage=0, duration=999999)


# ── 강화 Q: Geometric Verdict (광역 삼각자 강타 — 가렌 궁 느낌) ─────────────
class GeometricVerdict(_DomainOnlyMixin, DecisiveStrike):
    DISPLAY_NAME = "Geometric Verdict"
    DESCRIPTION  = "Domain — Giant triangle slam with area damage."
    COOLDOWN_SEC = 4.0
    HIT_FRAME    = 6
    ATK_FRAMES   = 26

    def __init__(self):
        Skill.__init__(self, "Geometric Verdict", damage=44,
                       cooldown=240, duration=26)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.0
        self._hit_done      = False
        self._speed_boosted = False
        self._cast_facing   = 1

    def get_hitbox(self, owner):
        if not self.active: return None
        elapsed = self.duration - self.timer
        if elapsed < self.HIT_FRAME or elapsed > self.HIT_FRAME + 10:
            return None
        # 더 넓은 판정
        w = int(owner.rect.w * 3.5)
        h = int(owner.rect.h * 2.2)
        facing = getattr(self, "_cast_facing", owner.facing)
        x = owner.rect.centerx if facing == 1 else owner.rect.centerx - w
        return pygame.Rect(x, owner.rect.centery - h//2, w, h)

    def on_start(self, owner, event_bus=None, psys=None):
        self._hit_done = False
        self._speed_boosted = False
        self._cast_facing = owner.facing
        if psys:
            for _ in range(20):
                ang = random.uniform(0, math.pi * 2)
                psys.spawn(owner.rect.centerx + math.cos(ang)*40,
                           owner.rect.centery + math.sin(ang)*40,
                           random.choice([(255,235,120),(255,200,60),(110,185,255)]),
                           count=1, speed=random.uniform(3,9),
                           gravity=0.1, life=random.randint(16,30), r=random.randint(4,8), glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        facing = getattr(self, "_cast_facing", owner.facing)
        target.vel.x += facing * 10
        target.vel.y -= 6
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        elapsed = self.duration - self.timer
        if elapsed < 3 or elapsed > self.HIT_FRAME + 14: return
        swing_t = min(1.0, elapsed / (self.HIT_FRAME + 6))
        facing  = getattr(self, "_cast_facing", owner.facing)
        angle   = -90 + swing_t * 180
        cx, cy  = dr.centerx + dr.w // 2 * facing, dr.centery + bob
        size    = int(dr.w * 3.0 * z)
        alpha   = _alpha(230 * (1 - abs(swing_t * 2 - 1) * 0.4))
        canvas = size * 5
        sf  = pygame.Surface((canvas, canvas), pygame.SRCALPHA)
        sc  = canvas // 2
        rad = math.radians(angle)
        pts = [
            (sc, sc),
            (sc + int(math.cos(rad) * size * 2.0) * facing,
             sc + int(math.sin(rad) * size * 2.0)),
            (sc + int(math.cos(rad + math.pi/2) * size * 1.2) * facing,
             sc + int(math.sin(rad + math.pi/2) * size * 1.2)),
        ]
        pygame.draw.polygon(sf, (255, 220, 60, _alpha(alpha * 0.35)), pts)
        pygame.draw.polygon(sf, (255, 250, 180, alpha), pts, max(3, int(4*z)))
        # 충격파 원
        for ri in range(3):
            pr = int(size * (0.5 + ri * 0.35) * swing_t)
            pygame.draw.circle(sf, (255, 235, 120, _alpha(alpha * 0.3 / (ri+1))),
                               (sc, sc), pr, max(1, int(2*z)))
        screen.blit(sf, (cx - sc, cy - sc))


# ── 강화 E: Infinite Spin (더 빠르고 강한 회전) ──────────────────────────────
class InfiniteSpin(_DomainOnlyMixin, JudgementSpin):
    DISPLAY_NAME = "Infinite Spin"
    DESCRIPTION  = "Domain — Faster, longer spin. Hits 10 times."
    COOLDOWN_SEC = 9.0
    SPIN_HITS    = 10
    HIT_INTERVAL = 5

    def __init__(self):
        Skill.__init__(self, "Infinite Spin", damage=22,
                       cooldown=540, duration=62)
        self.charge_value          = 0.0
        self.finisher_charge_value = 1.8
        self._spin_angle = 0.0
        self._hit_count  = 0
        self._hit_timer  = 0

    def on_update(self, owner, event_bus=None, psys=None):
        self._spin_angle += 18.0   # 더 빠른 회전
        self._hit_timer  += 1
        if self._hit_timer >= self.HIT_INTERVAL and self._hit_count < self.SPIN_HITS:
            self._hit_timer  = 0
            self._hit_count += 1
            self.has_hit = False
        if psys and self.timer % 2 == 0:
            ang = math.radians(self._spin_angle)
            r   = int(owner.rect.w * 1.6)
            psys.spawn(owner.rect.centerx + math.cos(ang) * r,
                       owner.rect.centery + math.sin(ang) * r,
                       random.choice([(255,235,120),(255,200,60),(200,180,255)]),
                       count=1, speed=3, gravity=0, life=10, r=5, glow=True)
            # 반대방향도
            psys.spawn(owner.rect.centerx - math.cos(ang) * r,
                       owner.rect.centery - math.sin(ang) * r,
                       (110, 185, 255), count=1, speed=2, gravity=0, life=8, r=4, glow=True)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        alpha = _alpha(200 + 50 * math.sin(self._spin_angle * 0.15))
        r     = int(dr.w * 1.8 * z)
        cx, cy = dr.centerx, dr.centery + bob
        sf    = pygame.Surface((r*2+20, r*2+20), pygame.SRCALPHA)
        sc    = r + 10
        # 두 개 삼각자 (60도 간격으로 회전)
        for off in (0, math.pi):
            ang = math.radians(self._spin_angle) + off
            p0  = (sc, sc)
            p1  = (sc + int(math.cos(ang) * r), sc + int(math.sin(ang) * r))
            p2  = (sc + int(math.cos(ang + math.pi/3) * r), sc + int(math.sin(ang + math.pi/3) * r))
            pygame.draw.polygon(sf, (255, 220, 60, _alpha(alpha * 0.2)), [p0, p1, p2])
            pygame.draw.lines(sf, (255, 250, 180, alpha), True, [p0, p1, p2], max(2, int(3*z)))
        pygame.draw.circle(sf, (255, 235, 120, _alpha(alpha * 0.5)), (sc, sc), r, max(1, int(2*z)))
        screen.blit(sf, (cx - sc, cy - sc))


# ── 캐릭터 클래스 ─────────────────────────────────────────────────────────────
class Pita(Player):
    WEIGHT     = 92;  KB_GROWTH = 85;  BASE_KB   = 28
    WALK_SPEED = 7.2; JUMP_POWER = -16.0; MAX_JUMPS = 2
    ATTACK_DMG = 11;  ATK_FRAMES = 18;   ATK_CD    = 30
    HIT_START  = 3;   HIT_END    = 14

    BODY_COLOR    = (55, 130, 230);  TRIM_COLOR  = (25, 65, 155)
    GLOW_COLOR    = (110, 185, 255); DARK_COLOR  = (20, 45, 110)
    DISPLAY_NAME  = "Pythagoras"
    DESCRIPTION   = "Geometric fighter inspired by Garen.\nStrike and spin with triangle rulers."
    PREVIEW_COLOR = (55, 130, 230)

    SPRITE_PATH   = "assets/images/charactor/pita/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/pita/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/pita/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/pita/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/pita/skill.png"
    SPRITE_SCALE  = 1.25; SPRITE_OFFSET_X = 0; SPRITE_OFFSET_Y = 6

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR; self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR; self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS; self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"]        = DecisiveStrike()
        self.skills["skill_E"]        = JudgementSpin()
        self.skills["skill_R"]        = PitaDomain()
        self.skills["skill_Q_domain"] = GeometricVerdict()
        self.skills["skill_E_domain"] = InfiniteSpin()

    def get_char_name(self): return "Pythagoras"
