"""
Einstein — 무겁고 강력, 한방 특화

일반 스킬 구성:
  Q / ;  basic   — Gravity Beam      (BeamSkill)       전방 중력 빔
  E / '  cc      — Black Hole        (SummonZoneSkill) 블랙홀 소환, 끌어당김
  R / /  domain  — Einstein Domain   (DomainUltimateSkill)

영역전개 중 스킬 (domain_active == True 일 때만 발동):
  Q / ;  domain  — Gravitational Collapse  빠른 강화 빔 (쿨타임 ↓, 데미지 ↑)
  E / '  domain  — Event Horizon           대형 블랙홀, 다단 흡입 + 히트
  W / '  domain  — Space-Time Rupture      근거리 시공간 폭발 (고데미지 넉백)
"""
from entities.player import Player
from systems.skill import (
    BeamSkill, SummonZoneSkill, EnhanceSkill,
    DomainUltimateSkill, Skill
)
import pygame
import math
import random


# ══════════════════════════════════════════════════════════════
#  공통 믹스인 — 영역 전개 중에만 발동
# ══════════════════════════════════════════════════════════════
class _DomainOnlyMixin:
    """can_activate를 오버라이드해 domain_active 중에만 쓸 수 있게 한다."""
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    """can_activate를 오버라이드해 domain_active가 아닐 때만 쓸 수 있게 한다."""
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


# ══════════════════════════════════════════════════════════════
#  일반 스킬 (영역 밖)
# ══════════════════════════════════════════════════════════════
class GravityBeam(_NormalOnlyMixin, BeamSkill):
    DISPLAY_NAME = "Gravity Beam"
    DESCRIPTION  = "Fire a heavy gravity beam.\nHigh damage, slow startup."
    BEAM_LENGTH  = 300
    BEAM_WIDTH   = 32
    BEAM_COLOR   = (255, 130, 110)
    BEAM_GLOW    = (255, 200, 180)
    COOLDOWN_SEC = 6.0

    def __init__(self):
        super().__init__("Gravity Beam", damage=35, cooldown=360, duration=28)


class BlackHole(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Black Hole"
    DESCRIPTION  = "Summon a black hole that pulls the enemy in."
    WARN_FRAMES  = 45
    ZONE_W       = 130
    ZONE_H       = 130
    ZONE_COLOR   = (225, 55, 55)
    ZONE_GLOW    = (255, 100, 80)
    COOLDOWN_SEC = 9.0

    def __init__(self):
        super().__init__("Black Hole", damage=20, cooldown=540, duration=100)

    def on_update(self, owner, event_bus=None, psys=None):
        if self.timer <= self.duration - self.WARN_FRAMES:
            zx = getattr(self, '_zone_x', owner.rect.centerx)
            zy = getattr(self, '_zone_y', owner.rect.bottom)
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
    SPEED_MULT    = 0.85
    DMG_BONUS     = 8
    ENHANCE_COLOR = (255, 130, 110)
    COOLDOWN_SEC  = 14.0

    def __init__(self):
        super().__init__("Mass Boost", damage=0, cooldown=840, duration=300)

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        owner._kb_resist = 0.5

    def on_end(self, owner):
        super().on_end(owner)
        if hasattr(owner, '_kb_resist'):
            del owner._kb_resist


# ══════════════════════════════════════════════════════════════
#  영역 전개 궁극기
# ══════════════════════════════════════════════════════════════
class EinsteinDomain(DomainUltimateSkill):
    DISPLAY_NAME          = "Einstein Domain"
    DESCRIPTION           = "Open Einstein's special domain.\nAll skills become stronger."
    DOMAIN_BG_PATH        = "assets/images/Einstein_domain.jpeg"
    DOMAIN_PARTICLE_COLOR = (255, 130, 110)
    BREAK_HITS            = 5
    CUTSCENE_FRAMES       = 30
    CUTSCENE_ZOOM         = 1.48
    TRANSITION_SPEED      = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Einstein Domain", damage=0, duration=999999)


# ══════════════════════════════════════════════════════════════
#  영역 전개 중 전용 스킬
# ══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# Q: Gravitational Collapse
#    일반 Gravity Beam의 강화판.
#    쿨타임 절반, 빔 길이 +50%, 데미지 +20, 색상 더 진하고 넓어짐.
# ─────────────────────────────────────────────────────────────
class GravitationalCollapse(_DomainOnlyMixin, BeamSkill):
    DISPLAY_NAME = "Gravitational Collapse"
    DESCRIPTION  = "Domain skill — Supercharged gravity beam.\nShorter cooldown, higher damage."
    BEAM_LENGTH  = 450        # +150px
    BEAM_WIDTH   = 52         # 더 넓음
    BEAM_COLOR   = (255, 60,  20)   # 더 진한 주황-빨
    BEAM_GLOW    = (255, 180, 80)
    COOLDOWN_SEC = 3.0

    def __init__(self):
        # has_hit 리셋 → 매 사용마다 1회 히트 허용
        super().__init__(
            "Gravitational Collapse",
            damage=55,          # 일반 35 → 55
            cooldown=180,       # 3초 (일반의 절반)
            duration=22,        # 살짝 짧은 지속
        )
        self.charge_value = 0.0           # 영역 중이므로 domain charge 불필요
        self.finisher_charge_value = 2.0  # 피니셔 게이지 2배 충전

    def on_start(self, owner, event_bus=None, psys=None):
        """발동 시 붉은 폭발 파티클."""
        if psys:
            for _ in range(18):
                psys.spawn(
                    owner.rect.centerx + owner.facing * 30,
                    owner.rect.centery,
                    (255, 100, 40),
                    count=1, speed=random.uniform(3, 7),
                    life=random.randint(12, 22), r=random.randint(3, 6),
                )

    def draw_front(self, owner, screen, camera, dr, bob, z):
        """빔 렌더링 — 이중 레이어(글로우 + 코어)."""
        if not self.active:
            return
        t      = self.timer / self.duration
        alpha  = int(240 * t)
        blen   = int(self.BEAM_LENGTH * z)
        bw_core = max(4, int(self.BEAM_WIDTH * t * z))
        bw_glow = bw_core + int(20 * z)

        bx = dr.right - int(6 * z) if owner.facing == 1 \
             else dr.left - blen + int(6 * z)
        cy = dr.centery + bob

        # 글로우 레이어
        glow_sf = pygame.Surface((blen, bw_glow + 4), pygame.SRCALPHA)
        pygame.draw.rect(
            glow_sf, (*self.BEAM_GLOW, int(alpha * 0.45)),
            (0, 0, blen, bw_glow + 4), border_radius=6
        )
        screen.blit(glow_sf, (bx, cy - (bw_glow + 4) // 2))

        # 코어 레이어
        core_sf = pygame.Surface((blen, bw_core), pygame.SRCALPHA)
        pygame.draw.rect(
            core_sf, (*self.BEAM_COLOR, alpha),
            (0, 0, blen, bw_core), border_radius=4
        )
        screen.blit(core_sf, (bx, cy - bw_core // 2))

        # 선단 섬광
        tip_x = bx + blen if owner.facing == 1 else bx
        flash_r = int((bw_core // 2 + 8) * t * z)
        if flash_r > 0:
            flash_sf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                flash_sf, (255, 240, 200, int(alpha * 0.7)),
                (flash_r, flash_r), flash_r
            )
            screen.blit(flash_sf, (tip_x - flash_r, cy - flash_r))


# ─────────────────────────────────────────────────────────────
# E: Event Horizon
#    일반 Black Hole 강화판.
#    영역이 2배 크고, 흡입력 강하며, 다단 히트(has_hit 리셋 반복).
#    경고 없이 즉발.
# ─────────────────────────────────────────────────────────────
class EventHorizon(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Event Horizon"
    DESCRIPTION  = "Domain skill — Massive black hole.\nMulti-hit pull, no warning."
    WARN_FRAMES  = 0            # 경고 프레임 없음 (즉발)
    ZONE_W       = 240          # 일반 130 → 240
    ZONE_H       = 240
    ZONE_COLOR   = (180, 30,  30)
    ZONE_GLOW    = (255, 80,  50)
    COOLDOWN_SEC = 7.0

    # 다단 히트 간격 (프레임)
    MULTI_HIT_INTERVAL = 20
    PULL_FORCE         = 5.0    # 흡입력 (일반 2.5 → 5.0)

    def __init__(self):
        super().__init__(
            "Event Horizon",
            damage=14,          # 다단히트니까 1회 데미지는 낮게
            cooldown=420,       # 7초
            duration=140,       # 일반보다 40프레임 더 지속
        )
        self.charge_value = 0.0
        self.finisher_charge_value = 1.5
        self._hit_timer  = 0    # 다단 히트용 타이머

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        self._hit_timer = 0
        # 소환 시 강렬한 파티클
        if psys:
            zx = getattr(self, '_zone_x', owner.rect.centerx)
            zy = getattr(self, '_zone_y', owner.rect.bottom) - self.ZONE_H // 2
            for _ in range(30):
                angle = random.uniform(0, math.pi * 2)
                spd   = random.uniform(2, 8)
                psys.spawn(
                    zx + int(math.cos(angle) * 40),
                    zy + int(math.sin(angle) * 40),
                    (200, 40, 40),
                    count=1, speed=spd,
                    life=random.randint(18, 35), r=random.randint(3, 7),
                )

    def on_update(self, owner, event_bus=None, psys=None):
        """매 프레임 흡입 + 주기적 다단 히트."""
        zx = getattr(self, '_zone_x', owner.rect.centerx)
        zy = getattr(self, '_zone_y', owner.rect.bottom) - self.ZONE_H // 2

        target = getattr(owner, '_skill_target', None)
        if target and not target.dead:
            dx   = zx - target.rect.centerx
            dy   = zy - target.rect.centery
            dist = max(1, (dx**2 + dy**2) ** 0.5)
            # 거리 기반 흡입 (가까울수록 강하게)
            pull = self.PULL_FORCE * (1.0 + 200 / max(dist, 80))
            target.vel.x += (dx / dist) * pull * 0.06
            target.vel.y += (dy / dist) * pull * 0.04

        # 다단 히트: MULTI_HIT_INTERVAL 프레임마다 has_hit 리셋
        self._hit_timer += 1
        if self._hit_timer >= self.MULTI_HIT_INTERVAL:
            self._hit_timer = 0
            self.has_hit    = False   # 다시 히트 허용

        # 파티클 — 나선형 잔상
        if psys and self.timer % 4 == 0:
            angle = (self.timer * 0.22) % (math.pi * 2)
            for i in range(3):
                a = angle + i * (math.pi * 2 / 3)
                r = random.randint(40, self.ZONE_W // 2)
                psys.spawn(
                    zx + int(math.cos(a) * r),
                    zy + int(math.sin(a) * r),
                    (200, 60, 60),
                    count=1, speed=random.uniform(1, 3),
                    life=random.randint(10, 20), r=random.randint(2, 5),
                )

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        """블랙홀 비주얼 — 동심원 펄스 + 중심 암흑."""
        if not self.active:
            return
        zx = getattr(self, '_zone_x', owner.rect.centerx)
        zy = getattr(self, '_zone_y', owner.rect.bottom) - self.ZONE_H // 2
        sx, sy = camera.world_to_screen(zx, zy)

        t       = self.timer / max(1, self.duration)
        base_r  = int(self.ZONE_W * 0.5 * z)
        pulse   = int(math.sin(pygame.time.get_ticks() * 0.008) * 12 * z)

        # 외곽 글로우 (여러 레이어)
        for layer_i, (radius_mult, alpha_base) in enumerate(
            [(1.6, 30), (1.3, 50), (1.0, 70)]
        ):
            r = int(base_r * radius_mult) + (pulse if layer_i == 0 else 0)
            if r <= 0:
                continue
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            col  = (180, 30, 30) if layer_i < 2 else (100, 15, 15)
            pygame.draw.circle(surf, (*col, alpha_base), (r, r), r)
            screen.blit(surf, (int(sx) - r, int(sy) - r))

        # 중심 암흑 (검정 코어)
        core_r = int(base_r * 0.45)
        if core_r > 0:
            core_sf = pygame.Surface((core_r * 2, core_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(core_sf, (0, 0, 0, 230), (core_r, core_r), core_r)
            screen.blit(core_sf, (int(sx) - core_r, int(sy) - core_r))

        # 회전 고리
        ring_r = int(base_r * 0.7 + pulse * 0.5)
        if ring_r > 0:
            ring_sf = pygame.Surface((ring_r * 2 + 8, ring_r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(
                ring_sf, (255, 80, 50, 120),
                (ring_r + 4, ring_r + 4), ring_r, max(1, int(4 * z))
            )
            screen.blit(ring_sf, (int(sx) - ring_r - 4, int(sy) - ring_r - 4))

    def get_hitbox(self, owner) -> pygame.Rect:
        zx = getattr(self, '_zone_x', owner.rect.centerx)
        zy = getattr(self, '_zone_y', owner.rect.bottom) - self.ZONE_H // 2
        return pygame.Rect(
            zx - self.ZONE_W // 2,
            zy - self.ZONE_H // 2,
            self.ZONE_W, self.ZONE_H,
        )


# ─────────────────────────────────────────────────────────────
# W (skill_2 슬롯): Space-Time Rupture
#    근거리 시공간 파열.  짧은 선딜 후 주변 방사형 폭발.
#    고데미지 + 강력 넉백.  영역 중에만 사용 가능.
# ─────────────────────────────────────────────────────────────
class SpaceTimeRupture(_DomainOnlyMixin, Skill):
    SKILL_TYPE   = "summon_zone"   # 도메인 차지 계산 방식 재활용
    DISPLAY_NAME = "Space-Time Rupture"
    DESCRIPTION  = "Domain skill — Tear spacetime nearby.\nHigh damage + strong knockback."
    COOLDOWN_SEC = 10.0

    # 폭발 반경 (월드 픽셀)
    BLAST_RADIUS  = 180
    # 선딜 프레임 (이 프레임 동안 히트박스 없음, 이펙트 표시)
    STARTUP_FRAMES = 18
    # 활성 히트박스 지속 프레임
    ACTIVE_FRAMES  = 12

    def __init__(self):
        super().__init__(
            "Space-Time Rupture",
            damage=70,
            cooldown=600,       # 10초
            duration=self.STARTUP_FRAMES + self.ACTIVE_FRAMES,
        )
        self.charge_value = 0.0
        self.finisher_charge_value = 3.0  # 피니셔 게이지 가장 많이 충전
        self._particles: list[dict] = []

    def on_start(self, owner, event_bus=None, psys=None):
        """선딜 시작 — 수렴하는 파티클 연출."""
        self._particles = []
        cx = owner.rect.centerx
        cy = owner.rect.centery
        # 바깥쪽에서 중심으로 모이는 파티클
        for _ in range(40):
            angle = random.uniform(0, math.pi * 2)
            dist  = random.uniform(80, self.BLAST_RADIUS)
            self._particles.append({
                "x": cx + math.cos(angle) * dist,
                "y": cy + math.sin(angle) * dist,
                "tx": cx, "ty": cy,   # 목표(중심)
                "life": self.STARTUP_FRAMES + 6,
                "max_life": self.STARTUP_FRAMES + 6,
                "color": random.choice([
                    (255, 100, 50), (255, 200, 80), (200, 50, 200)
                ]),
                "r": random.randint(3, 7),
                "phase": "gather",    # gather → explode
            })

    def on_update(self, owner, event_bus=None, psys=None):
        remaining = self.timer  # 남은 프레임 (duration → 0)
        active_start = self.ACTIVE_FRAMES  # timer가 이 값일 때 폭발 시작

        # 파티클 업데이트
        alive = []
        cx = owner.rect.centerx
        cy = owner.rect.centery
        for p in self._particles:
            p["life"] -= 1
            if p["life"] <= 0:
                continue
            if p["phase"] == "gather":
                # 중심으로 이동
                dx = p["tx"] - p["x"]
                dy = p["ty"] - p["y"]
                p["x"] += dx * 0.18
                p["y"] += dy * 0.18
            else:
                # 바깥으로 폭발
                dx = p["x"] - cx
                dy = p["y"] - cy
                dist = max(1, (dx**2 + dy**2)**0.5)
                spd  = 8 + (p["max_life"] - p["life"]) * 0.4
                p["x"] += (dx / dist) * spd
                p["y"] += (dy / dist) * spd
            alive.append(p)
        self._particles = alive

        # 폭발 순간: ACTIVE_FRAMES 진입 시 파티클 전환 + psys 폭발
        if remaining == self.ACTIVE_FRAMES:
            for p in self._particles:
                p["phase"] = "explode"
                p["life"]  = 20
                p["max_life"] = 20
            # 강렬한 추가 파티클 방사
            if psys:
                for _ in range(50):
                    angle = random.uniform(0, math.pi * 2)
                    psys.spawn(
                        cx + int(math.cos(angle) * 10),
                        cy + int(math.sin(angle) * 10),
                        random.choice([(255, 80, 20), (255, 220, 80), (180, 40, 220)]),
                        count=1,
                        speed=random.uniform(5, 14),
                        life=random.randint(18, 30),
                        r=random.randint(4, 9),
                    )

    def get_hitbox(self, owner) -> pygame.Rect | None:
        """ACTIVE_FRAMES 동안만 히트박스 활성."""
        if not self.active:
            return None
        if self.timer > self.ACTIVE_FRAMES:
            return None   # 선딜 중
        r = self.BLAST_RADIUS
        return pygame.Rect(
            owner.rect.centerx - r,
            owner.rect.centery - r,
            r * 2, r * 2,
        )

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        """수렴 → 폭발 비주얼."""
        if not self.active:
            return

        cx_w = owner.rect.centerx
        cy_w = owner.rect.centery
        sx, sy = camera.world_to_screen(cx_w, cy_w)

        remaining = self.timer
        total     = self.STARTUP_FRAMES + self.ACTIVE_FRAMES

        # ── 선딜: 수렴 링 ──
        if remaining > self.ACTIVE_FRAMES:
            progress = 1.0 - (remaining - self.ACTIVE_FRAMES) / self.STARTUP_FRAMES
            ring_r   = int(self.BLAST_RADIUS * (1.0 - progress * 0.6) * z)
            alpha    = int(80 + 120 * progress)
            if ring_r > 0:
                ring_sf = pygame.Surface((ring_r * 2 + 6, ring_r * 2 + 6), pygame.SRCALPHA)
                thick   = max(2, int((3 + 5 * progress) * z))
                pygame.draw.circle(
                    ring_sf, (200, 60, 220, alpha),
                    (ring_r + 3, ring_r + 3), ring_r, thick
                )
                screen.blit(ring_sf, (int(sx) - ring_r - 3, int(sy) - ring_r - 3 + int(bob)))

                # 내부 보조 링
                inner_r = ring_r // 2
                if inner_r > 0:
                    inner_sf = pygame.Surface((inner_r * 2 + 4, inner_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(
                        inner_sf, (255, 150, 60, int(alpha * 0.6)),
                        (inner_r + 2, inner_r + 2), inner_r,
                        max(1, int(2 * z))
                    )
                    screen.blit(inner_sf, (int(sx) - inner_r - 2, int(sy) - inner_r - 2 + int(bob)))

        # ── 폭발: 방사형 플래시 ──
        else:
            blast_t  = 1.0 - remaining / self.ACTIVE_FRAMES   # 0 → 1
            blast_r  = int(self.BLAST_RADIUS * (0.3 + blast_t * 0.7) * z)
            alpha    = int(220 * (1.0 - blast_t))
            if blast_r > 0:
                surf = pygame.Surface((blast_r * 2, blast_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 120, 40, alpha), (blast_r, blast_r), blast_r)
                screen.blit(surf, (int(sx) - blast_r, int(sy) - blast_r + int(bob)))

                core_r = blast_r // 3
                if core_r > 0:
                    core_sf = pygame.Surface((core_r * 2, core_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(
                        core_sf, (255, 255, 200, min(255, alpha + 60)),
                        (core_r, core_r), core_r
                    )
                    screen.blit(core_sf, (int(sx) - core_r, int(sy) - core_r + int(bob)))

        # ── 수렴/폭발 파티클 ──
        for p in self._particles:
            if p["life"] <= 0:
                continue
            px, py = camera.world_to_screen(p["x"], p["y"])
            alpha  = int(220 * p["life"] / max(1, p["max_life"]))
            r      = max(1, int(p["r"] * z))
            psurf  = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(psurf, (*p["color"], alpha), (r, r), r)
            screen.blit(psurf, (int(px) - r, int(py) - r))


# ══════════════════════════════════════════════════════════════
#  Einstein 캐릭터
# ══════════════════════════════════════════════════════════════
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
    DESCRIPTION   = (
        "Heavy hitter with massive knockback.\n"
        "Slow but devastating.\n"
        "Domain unlocks 3 special skills."
    )
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
        "basic":   ("Gravity Beam",  "BeamSkill",      35, 40, 6.0),
        "cc":      ("Black Hole",    "SummonZoneSkill", 20, 45, 9.0),
        "enhance": ("Mass Boost",    "EnhanceSkill",     0, 40, 14.0),
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
        # 일반 스킬
        self.skills["skill_Q"] = GravityBeam()        # Q / ;  (영역 밖)
        self.skills["skill_E"] = BlackHole()           # E / '  (영역 밖)

        # 영역 전개 궁극기
        self.skills["skill_R"] = EinsteinDomain()      # R / /

        # 영역 전개 중 스킬 (같은 키에 덮어쓰기 방식이 아닌 병렬 등록)
        # Player.use_skill()은 can_activate()를 거치므로
        # 영역 밖에선 Normal 스킬, 영역 중엔 Domain 스킬이 선택됨.
        # → 같은 슬롯에 두 스킬을 리스트로 묶어 관리
        self.skills["skill_Q_domain"] = GravitationalCollapse()   # Q (영역 중)
        self.skills["skill_E_domain"] = EventHorizon()            # E (영역 중)
        self.skills["skill_W_domain"] = SpaceTimeRupture()        # W (영역 중, 신규 키)

    # ── 스킬 사용 오버라이드 ──────────────────────────────────
    def use_skill(self, skill_key: str, event_bus=None, psys=None) -> bool:
        """
        영역 중에는 domain 버전 스킬 우선 시도.
        영역 밖이거나 domain 스킬 쿨타임이면 일반 스킬 시도.
        """
        domain_key = skill_key + "_domain"
        if domain_key in self.skills:
            domain_skill = self.skills[domain_key]
            if domain_skill.can_use(self):
                domain_skill.use(self, event_bus, psys)
                self.active_skill = domain_skill
                return True

        # 일반 스킬 fallback
        skill = self.skills.get(skill_key)
        if skill and skill.can_use(self):
            skill.use(self, event_bus, psys)
            self.active_skill = skill
            return True

        return False

    def get_char_name(self):
        return "Einstein"