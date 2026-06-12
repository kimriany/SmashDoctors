"""
Schrodinger — 원자 궤도와 파동 간섭으로 공간을 제어하는 콤보 캐릭터.

일반 스킬:
  Q / ;  Atomic Wave       — ProjectileSkill, 사인파로 이동하는 원자 발사체
  E / '  Interference Well — SummonZoneSkill, 파동 간섭 필드
  R / /  Superposition     — schrodinger_domain.png 영역 전개

영역 전개 중 강화 스킬:
  Q / ;  Quantum Packet    — 더 빠르고 강한 파동 발사체
  E / '  Probability Cloud — 넓은 다단 파동 필드
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


DOMAIN_BG = "assets/images/charactor/Schrödinger/schrodinger_domain.png"
ATOM_COLORS = (
    (90, 210, 255),
    (160, 120, 255),
    (235, 245, 255),
    (80, 255, 210),
)


def _alpha(value):
    return max(0, min(255, int(value)))


def _apply_cd_accel(owner, source_skill, mult):
    extra = max(0.0, mult - 1.0)
    if extra <= 0:
        owner._cd_accel_active = False
        owner._cd_accel_mult = 1.0
        return

    source_skill._cd_accum = getattr(source_skill, "_cd_accum", 0.0) + extra
    bonus = int(source_skill._cd_accum)
    if bonus >= 1:
        source_skill._cd_accum -= bonus
        for sk in owner.skills.values():
            if sk is not source_skill and sk.current_cooldown > 0:
                sk.current_cooldown = max(0, sk.current_cooldown - bonus)
    owner._cd_accel_active = True
    owner._cd_accel_mult = mult


class _DomainOnlyMixin:
    def can_activate(self, owner) -> bool:
        return getattr(owner, "domain_active", False)


class _NormalOnlyMixin:
    def can_activate(self, owner) -> bool:
        return not getattr(owner, "domain_active", False)


class AtomicWave(_NormalOnlyMixin, ProjectileSkill):
    DISPLAY_NAME = "Atomic Wave"
    DESCRIPTION = "Fire an atom packet with a wave trail."
    PROJ_SPEED = 10.0
    PROJ_SIZE = 17
    PROJ_COLOR = (95, 220, 255)
    PROJ_GLOW = (210, 245, 255)
    COOLDOWN_SEC = 3.5

    def __init__(self):
        super().__init__("Atomic Wave", damage=18, cooldown=210, duration=84)
        self.charge_value = 0.9

    def on_start(self, owner, event_bus=None, psys=None):
        self._origin_y = float(owner.rect.centery - 6)
        self._px = float(owner.rect.centerx + owner.facing * 30)
        self._py = self._origin_y
        self._vx = self.PROJ_SPEED * owner.facing
        self._phase = random.uniform(0, math.pi * 2)
        self._alive = True
        if psys:
            psys.spawn(self._px, self._py, (90, 210, 255), count=14,
                       speed=4.5, gravity=-0.04, life=24, r=4, glow=True)
            psys.spawn(self._px, self._py, (170, 120, 255), count=8,
                       speed=3.2, gravity=-0.02, life=20, r=3, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive:
            return
        elapsed = self.duration - self.timer
        self._px += self._vx
        self._py = self._origin_y

        if psys and self.timer % 3 == 0:
            wave_y = self._py + math.sin(elapsed * 0.34 + self._phase) * 22
            psys.spawn(self._px - owner.facing * 14, wave_y,
                       random.choice(ATOM_COLORS), count=2, speed=2.0,
                       gravity=-0.03, life=18, r=3, glow=True)
        if abs(self._px - owner.rect.centerx) > 760:
            self._alive = False

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._alive = False
        target.vel.y -= 4
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, (90, 220, 255),
                       count=24, speed=7, gravity=-0.06, life=30, r=5, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery, (190, 130, 255),
                       count=16, speed=5, gravity=-0.02, life=24, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active or not getattr(self, "_alive", False):
            return

        sx, sy = camera.world_to_screen(self._px, self._py)
        r = max(5, int(self.PROJ_SIZE * z))
        elapsed = self.duration - self.timer

        # 파동 궤적
        points = []
        mirror_points = []
        for i in range(18):
            x = sx - owner.facing * i * 9 * z
            y = sy + math.sin(elapsed * 0.34 - i * 0.55 + self._phase) * 11 * z
            y2 = sy - math.sin(elapsed * 0.34 - i * 0.55 + self._phase) * 11 * z
            points.append((x, y))
            mirror_points.append((x, y2))
        if len(points) > 1:
            bounds = pygame.Rect(0, 0, screen.get_width(), screen.get_height())
            wave = pygame.Surface(bounds.size, pygame.SRCALPHA)
            pygame.draw.lines(wave, (95, 220, 255, 150), False, points, max(1, int(2 * z)))
            pygame.draw.lines(wave, (180, 120, 255, 105), False, mirror_points, max(1, int(2 * z)))
            screen.blit(wave, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # 원자 궤도 링
        ring = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
        cx = cy = r * 5 // 2
        pygame.draw.circle(ring, (20, 28, 70, 130), (cx, cy), int(r * 1.1))
        pygame.draw.circle(ring, (230, 250, 255, 230), (cx, cy), max(2, r // 3))
        for i, angle in enumerate((0, math.pi / 3, -math.pi / 3)):
            rect = pygame.Rect(cx - int(r * 1.8), cy - int(r * 0.58), int(r * 3.6), int(r * 1.16))
            orbit = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
            pygame.draw.ellipse(orbit, (*ATOM_COLORS[i], 135), rect, max(1, int(2 * z)))
            rotated = pygame.transform.rotate(orbit, math.degrees(angle) + elapsed * 7)
            screen.blit(rotated, (sx - rotated.get_width() // 2, sy - rotated.get_height() // 2),
                        special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(ring, (sx - cx, sy - cy), special_flags=pygame.BLEND_RGBA_ADD)


class QuantumCollapseZone(_NormalOnlyMixin, SummonZoneSkill):
    """
    슈뢰딩거 E — Quantum Collapse Zone

    양자 중첩 구역을 소환한다.
    구역은 두 가지 상태로 존재:

    [미관측 상태] 상대가 없을 때:
      - 희미하게 진동하는 확률 파동 이펙트
      - 슈뢰딩거가 구역 안에 있으면 스킬 쿨타임 가속 (×1.5)

    [붕괴 상태] 상대가 구역에 진입하는 순간:
      - 파동 함수 붕괴 이펙트 (링 폭발)
      - 상대를 랜덤 방향으로 강하게 튕김 (확률적 CC)
      - 구역 소멸
    """
    DISPLAY_NAME  = "Quantum Collapse Zone"
    DESCRIPTION   = "Summon a quantum zone.\nCollapses violently when observed."
    WARN_FRAMES   = 0
    ZONE_W        = 200
    ZONE_H        = 200
    ZONE_COLOR    = (140, 60, 255)
    ZONE_GLOW     = (210, 150, 255)
    COOLDOWN_SEC  = 9.0

    CD_ACCEL_MULT = 1.5    # 구역 안에서 쿨타임 가속 배율
    COLLAPSE_DMG  = 22     # 붕괴 시 데미지

    def __init__(self):
        super().__init__("Quantum Collapse Zone", damage=self.COLLAPSE_DMG,
                         cooldown=540, duration=420)
        self.charge_value    = 1.2
        self._collapsed      = False   # 붕괴 발동 여부
        self._collapse_frame = 0       # 붕괴 연출 프레임
        self._phase          = 0.0
        self._wave_rings     = []      # 붕괴 링 이펙트 목록
        self._cd_accum       = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        self._zone_x = owner.rect.centerx + owner.facing * 180
        self._zone_y = owner.rect.centery

        self._phase       = random.uniform(0, math.pi * 2)
        self._collapsed   = False
        self._collapse_frame = 0
        self._wave_rings  = []
        self._cd_accum    = 0.0
        self.has_hit      = False

        if psys:
            # 소환 이펙트: 확률 파동 링
            for r_val in (30, 55, 80):
                for i in range(16):
                    ang = (i / 16) * math.pi * 2
                    psys.spawn(
                        self._zone_x + math.cos(ang) * r_val,
                        self._zone_y + math.sin(ang) * r_val,
                        random.choice(ATOM_COLORS),
                        count=1, speed=1.8, gravity=-0.04, life=28, r=3, glow=True
                    )

    def get_hitbox(self, owner):
        if not self.active or self._collapsed:
            return None
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.centery)
        r  = self.ZONE_W // 2
        return pygame.Rect(zx - r, zy - r, r * 2, r * 2)

    def on_update(self, owner, event_bus=None, psys=None):
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.centery)

        # 붕괴 연출 진행 중
        if self._collapsed:
            self._collapse_frame += 1
            owner._cd_accel_active = False   # 붕괴 시 가속 즉시 중단
            owner._cd_accel_mult = 1.0
            for ring in self._wave_rings:
                ring["r"]    += ring["speed"]
                ring["alpha"] = max(0, ring["alpha"] - ring["decay"])
            self._wave_rings = [r for r in self._wave_rings if r["alpha"] > 0]
            return

        # ── 미관측 상태: 쿨타임 가속 ──
        # 기본 감소(1/f)에 더해 매 프레임 (CD_ACCEL_MULT-1)만큼 추가 감소
        # 누적 오차 방지를 위해 _cd_accel_accum 사용
        zone = self.get_hitbox(owner)
        if zone and zone.colliderect(owner.rect):
            _apply_cd_accel(owner, self, self.CD_ACCEL_MULT)
        else:
            self._cd_accum = 0.0
            owner._cd_accel_active = False
            owner._cd_accel_mult = 1.0

        # ── 상대가 진입하면 붕괴 ──
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and zone and zone.colliderect(target.rect):
            self._trigger_collapse(owner, target, event_bus, psys)

        # ── 파동 파티클 ──
        if psys and self.timer % 7 == 0:
            ang = random.uniform(0, math.pi * 2)
            r   = random.uniform(self.ZONE_W * 0.1, self.ZONE_W * 0.45)
            psys.spawn(
                zx + math.cos(ang) * r, zy + math.sin(ang) * r,
                random.choice(ATOM_COLORS),
                count=1, speed=random.uniform(0.4, 1.8),
                gravity=-0.03, life=random.randint(16, 28), r=random.randint(2, 4),
                glow=True
            )

    def _trigger_collapse(self, owner, target, event_bus, psys):
        """파동 함수 붕괴 — 상대를 랜덤 방향으로 튕김."""
        if self.has_hit:
            return
        self._collapsed = True
        self.has_hit    = True

        # 붕괴 링 이펙트 생성
        for i in range(5):
            self._wave_rings.append({
                "r": 10 + i * 15, "speed": 6 + i * 2,
                "alpha": 255 - i * 35, "decay": 8 + i * 3,
                "color": ATOM_COLORS[i % len(ATOM_COLORS)],
            })

        # 확률적 CC: 랜덤 방향 넉백
        angle = random.uniform(0, math.pi * 2)
        kb    = 14 + target.damage_pct * 0.06
        target.vel.x = math.cos(angle) * kb
        target.vel.y = math.sin(angle) * kb - 5
        target.invincible = max(target.invincible, 16)

        if event_bus:
            event_bus.emit("attack_hit", {
                "attacker": owner, "target": target,
                "damage": self.COLLAPSE_DMG, "is_skill": True,
                "particle_system": psys, "floater_system": None,
            })

        if psys:
            zx = getattr(self, "_zone_x", owner.rect.centerx)
            zy = getattr(self, "_zone_y", owner.rect.centery)
            # 대폭발 파티클
            for col in ATOM_COLORS:
                psys.spawn(zx, zy, col, count=20, speed=9,
                           gravity=-0.05, life=38, r=6, glow=True)
            psys.spawn(zx, zy, (255, 255, 255), count=12, speed=6,
                       gravity=-0.08, life=22, r=4, glow=True)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.centery)
        sx, sy = camera.world_to_screen(zx, zy)
        tick   = pygame.time.get_ticks()
        t      = self.timer / max(1, self.duration)

        # ── 붕괴 링 렌더 ──
        if self._collapsed:
            for ring in self._wave_rings:
                r_px = int(ring["r"] * z)
                if r_px < 2:
                    continue
                ring_sf = pygame.Surface((r_px*2+4, r_px*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ring_sf, (*ring["color"], _alpha(ring["alpha"])),
                                   (r_px+2, r_px+2), r_px, max(1, int(3*z)))
                screen.blit(ring_sf, (sx - r_px - 2, sy - r_px - 2))
            return

        # ── 미관측 구역 렌더 ──
        base_r = int(self.ZONE_W * 0.5 * z)
        pulse  = math.sin(tick * 0.006 + self._phase)
        alpha  = int(max(20, 75 * t))

        # 중심 안개 원
        core = pygame.Surface((base_r*2+20, base_r*2+20), pygame.SRCALPHA)
        cr   = base_r + 10
        pygame.draw.circle(core, (60, 10, 120, int(alpha*0.4)), (cr, cr), base_r)
        screen.blit(core, (sx-cr, sy-cr))

        # 확률 파동 링 (3겹, 서로 다른 속도로 진동)
        for i, (freq, amp, col) in enumerate([
            (0.005, 8, (170, 80, 255)),
            (0.008, 5, (100, 180, 255)),
            (0.012, 3, (220, 150, 255)),
        ]):
            wave_r = int((base_r + math.sin(tick * freq + self._phase + i*1.2) * amp * z) * z / z)
            ring_s = pygame.Surface((wave_r*2+8, wave_r*2+8), pygame.SRCALPHA)
            pygame.draw.circle(ring_s, (*col, _alpha(alpha - i*15)),
                               (wave_r+4, wave_r+4), wave_r, max(1, int((3-i)*z)))
            screen.blit(ring_s, (sx-wave_r-4, sy-wave_r-4))

        # 내부 양자 심볼 (ψ 느낌 — 교차 타원)
        sym_r = int(base_r * 0.55)
        sym_s = pygame.Surface((sym_r*2+10, sym_r*2+10), pygame.SRCALPHA)
        sc, ss = sym_r+5, sym_r+5
        rot    = tick * 0.025
        for angle_off, col in ((0, (200,120,255)), (math.pi/3, (120,200,255)),
                               (-math.pi/3, (255,180,100))):
            ew, eh = int(sym_r*1.8), int(sym_r*0.55)
            el_s = pygame.Surface((ew+4, eh+4), pygame.SRCALPHA)
            pygame.draw.ellipse(el_s, (*col, int(alpha*0.7)),
                                (2, 2, ew, eh), max(1, int(2*z)))
            rotated = pygame.transform.rotate(el_s,
                          math.degrees(rot + angle_off))
            sym_s.blit(rotated,
                       (sc - rotated.get_width()//2,
                        ss - rotated.get_height()//2),
                       special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(sym_s, (sx-sc, sy-ss))

        # "?" 레이블 (미관측 상태 표시)
        fnt  = pygame.font.SysFont(None, int(28*z), bold=True)
        qlbl = fnt.render("?", True, (200, 140, 255))
        qlbl.set_alpha(_alpha(alpha * 1.4))
        screen.blit(qlbl, (sx - qlbl.get_width()//2, sy - qlbl.get_height()//2))

    def on_end(self, owner):
        self._cd_accum = 0.0
        owner._cd_accel_active = False
        owner._cd_accel_mult = 1.0


class SchrodingerDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Superposition Domain"
    DESCRIPTION = "Open Schrodinger's quantum domain."
    DOMAIN_BG_PATH = DOMAIN_BG
    DOMAIN_PARTICLE_COLOR = (170, 120, 255)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 32
    CUTSCENE_ZOOM = 1.46
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Superposition Domain", damage=0, duration=999999)


class QuantumPacket(_DomainOnlyMixin, AtomicWave):
    DISPLAY_NAME = "Quantum Packet"
    DESCRIPTION = "Domain skill — faster atom wave with stronger collapse."
    PROJ_SPEED = 14.0
    PROJ_SIZE = 22
    COOLDOWN_SEC = 2.6

    def __init__(self):
        ProjectileSkill.__init__(self, "Quantum Packet", damage=32, cooldown=156, duration=76)
        self.charge_value = 0.0
        self.finisher_charge_value = 1.7

    def on_start(self, owner, event_bus=None, psys=None):
        super().on_start(owner, event_bus, psys)
        if psys:
            for _ in range(24):
                psys.spawn(self._px, self._py, random.choice(ATOM_COLORS),
                           count=1, speed=random.uniform(3, 8), gravity=-0.05,
                           life=random.randint(18, 32), r=random.randint(3, 6), glow=True)


class ProbabilityStorm(_DomainOnlyMixin, SummonZoneSkill):
    """
    슈뢰딩거 영역 강화 E — Probability Storm

    영역 전개 중 사용.
    넓은 확률 폭풍을 소환해 상대를 중심으로 끌어당기다가
    일정 시간 후 대폭발로 사방으로 날려버린다.

    Phase 1 (0~60f): 경고 없이 바로 중력 흡수 시작
    Phase 2 (60~90f): 폭발 예고 (링 확장)
    Phase 3 (90f):    대폭발 + 방사형 넉백
    """
    DISPLAY_NAME      = "Probability Storm"
    DESCRIPTION       = "Domain skill — gravitational collapse,\nthen explosive detonation."
    WARN_FRAMES       = 0
    ZONE_W            = 320
    ZONE_H            = 320
    ZONE_COLOR        = (100, 40, 220)
    ZONE_GLOW         = (200, 140, 255)
    COOLDOWN_SEC      = 10.0

    PULL_FORCE        = 3.2    # 흡수 강도 (프레임당 px)
    EXPLODE_FRAME     = 180    # 폭발 프레임
    EXPLODE_KB        = 26     # 폭발 넉백
    EXPLODE_RADIUS    = 110
    CD_ACCEL_MULT     = 2.0

    def __init__(self):
        super().__init__("Probability Storm", damage=35, cooldown=600, duration=300)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.0
        self._exploded             = False
        self._phase                = 0.0
        self._explode_rings        = []
        self._cd_accum             = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        self._zone_x = owner.rect.centerx + owner.facing * 180
        self._zone_y = owner.rect.centery
        self._phase    = random.uniform(0, math.pi * 2)
        self._exploded = False
        self._explode_rings = []
        self._cd_accum = 0.0
        self.has_hit   = False

        if psys:
            for _ in range(40):
                ang = random.uniform(0, math.pi * 2)
                r   = random.uniform(30, 140)
                psys.spawn(
                    self._zone_x + math.cos(ang) * r,
                    self._zone_y + math.sin(ang) * r,
                    random.choice(ATOM_COLORS),
                    count=1, speed=random.uniform(2, 6),
                    gravity=-0.04, life=random.randint(24, 44), r=random.randint(3, 7),
                    glow=True
                )

    def get_hitbox(self, owner):
        if not self.active:
            return None
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.centery)
        r  = self.ZONE_W // 2
        return pygame.Rect(zx - r, zy - r, r * 2, r * 2)

    def on_update(self, owner, event_bus=None, psys=None):
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.centery)
        elapsed = self.duration - self.timer
        target  = getattr(owner, "_skill_target", None)

        # 폭발 링 업데이트
        for ring in self._explode_rings:
            ring["r"]    += ring["speed"]
            ring["alpha"] = max(0, ring["alpha"] - ring["decay"])
        self._explode_rings = [r for r in self._explode_rings if r["alpha"] > 0]

        if self._exploded:
            self._cd_accum = 0.0
            owner._cd_accel_active = False
            owner._cd_accel_mult = 1.0
            return

        # Phase 1: 중력 흡수
        if elapsed < self.EXPLODE_FRAME:
            zone = self.get_hitbox(owner)
            if zone and zone.colliderect(owner.rect):
                _apply_cd_accel(owner, self, self.CD_ACCEL_MULT)
            else:
                self._cd_accum = 0.0
                owner._cd_accel_active = False
                owner._cd_accel_mult = 1.0

            if target and not target.dead:
                if zone and zone.colliderect(target.rect):
                    dx = zx - target.rect.centerx
                    dy = zy - target.rect.centery
                    dist = max(1, math.sqrt(dx*dx + dy*dy))
                    pull = self.PULL_FORCE * (1 + elapsed / self.EXPLODE_FRAME)
                    target.vel.x += (dx / dist) * pull * 0.3
                    target.vel.y += (dy / dist) * pull * 0.3

            # 파티클 (안으로 빨려드는 느낌)
            if psys and self.timer % 4 == 0:
                ang = random.uniform(0, math.pi * 2)
                r   = random.uniform(self.ZONE_W * 0.3, self.ZONE_W * 0.5)
                vx  = -math.cos(ang) * 4
                vy  = -math.sin(ang) * 4
                psys.spawn(
                    zx + math.cos(ang) * r, zy + math.sin(ang) * r,
                    random.choice(ATOM_COLORS),
                    count=1, speed=0, gravity=0, life=16, r=4, glow=True
                )

        # Phase 2: 폭발
        if elapsed >= self.EXPLODE_FRAME and not self._exploded:
            self._do_explode(owner, target, event_bus, psys, zx, zy)

    def _do_explode(self, owner, target, event_bus, psys, zx, zy):
        self._exploded = True
        self.has_hit   = True
        self._cd_accum = 0.0
        owner._cd_accel_active = False
        owner._cd_accel_mult = 1.0

        # 폭발 링 5겹
        for i in range(6):
            self._explode_rings.append({
                "r": 5 + i * 8, "speed": 10 + i * 3,
                "alpha": 255 - i * 30, "decay": 6 + i * 2,
                "color": ATOM_COLORS[i % len(ATOM_COLORS)],
            })

        if target and not target.dead:
            # 방사형 날려보내기
            dx  = target.rect.centerx - zx
            dy  = target.rect.centery - zy
            dist = max(1, math.sqrt(dx*dx + dy*dy))
            if dist <= self.EXPLODE_RADIUS:
                kb  = self.EXPLODE_KB + target.damage_pct * 0.08
                target.vel.x = (dx / dist) * kb
                target.vel.y = (dy / dist) * kb - 8

                if event_bus:
                    event_bus.emit("attack_hit", {
                        "attacker": owner, "target": target,
                        "damage": self.damage, "is_skill": True,
                        "particle_system": psys, "floater_system": None,
                    })

        if psys:
            for col in ATOM_COLORS:
                psys.spawn(zx, zy, col, count=28, speed=11,
                           gravity=-0.04, life=44, r=7, glow=True)
            psys.spawn(zx, zy, (255, 255, 255), count=16, speed=8,
                       gravity=-0.06, life=28, r=5, glow=True)

    def on_end(self, owner):
        self._cd_accum = 0.0
        owner._cd_accel_active = False
        owner._cd_accel_mult = 1.0

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        zx = getattr(self, "_zone_x", owner.rect.centerx)
        zy = getattr(self, "_zone_y", owner.rect.centery)
        sx, sy = camera.world_to_screen(zx, zy)
        elapsed = self.duration - self.timer
        tick    = pygame.time.get_ticks()

        # 폭발 링 렌더
        for ring in self._explode_rings:
            r_px = int(ring["r"] * z)
            if r_px < 2:
                continue
            rs = pygame.Surface((r_px*2+6, r_px*2+6), pygame.SRCALPHA)
            pygame.draw.circle(rs, (*ring["color"], _alpha(ring["alpha"])),
                               (r_px+3, r_px+3), r_px, max(1, int(4*z)))
            screen.blit(rs, (sx-r_px-3, sy-r_px-3))

        if self._exploded:
            return

        base_r = int(self.ZONE_W * 0.5 * z)
        phase2 = elapsed >= self.EXPLODE_FRAME * 0.7
        t      = min(1.0, elapsed / max(1, self.EXPLODE_FRAME))
        pulse  = math.sin(tick * (0.01 + t * 0.02) + self._phase)

        # 중심 블랙홀
        core_r = int(base_r * (0.18 + 0.12 * pulse))
        cs     = pygame.Surface((core_r*2+8, core_r*2+8), pygame.SRCALPHA)
        pygame.draw.circle(cs, (20, 5, 50, 200), (core_r+4, core_r+4), core_r)
        pygame.draw.circle(cs, (160, 80, 255, 180), (core_r+4, core_r+4), core_r, max(2,int(3*z)))
        screen.blit(cs, (sx-core_r-4, sy-core_r-4))

        # 흡수 소용돌이 링 (Phase 1)
        spiral_count = 3 if not phase2 else 6
        for i in range(spiral_count):
            frac  = 0.3 + 0.7 * (i / spiral_count)
            r_val = int(base_r * frac)
            alpha = int(max(20, (120 - i * 15) * t))
            rot   = tick * (0.018 - i * 0.003) * (-1 if i % 2 else 1)
            rs    = pygame.Surface((r_val*2+8, r_val*2+8), pygame.SRCALPHA)
            # 점선 링 느낌 (호 8개)
            for seg in range(8):
                start_ang = rot + seg * math.pi / 4
                end_ang   = start_ang + math.pi / 5
                pts = []
                for a in [start_ang + k*(end_ang-start_ang)/8 for k in range(9)]:
                    pts.append((r_val+4 + int(r_val * math.cos(a)),
                                r_val+4 + int(r_val * math.sin(a))))
                if len(pts) > 1:
                    pygame.draw.lines(rs, (*ATOM_COLORS[i % len(ATOM_COLORS)], alpha),
                                      False, pts, max(1, int(2*z)))
            screen.blit(rs, (sx-r_val-4, sy-r_val-4))

        # Phase 2: 폭발 예고 링 (빠르게 팽창)
        if phase2:
            max_warn_r = int(self.EXPLODE_RADIUS * z)
            warn_r = int(max_warn_r * (0.5 + 0.5 * ((elapsed - self.EXPLODE_FRAME*0.7) /
                                                    (self.EXPLODE_FRAME*0.3))))
            ws = pygame.Surface((warn_r*2+10, warn_r*2+10), pygame.SRCALPHA)
            pygame.draw.circle(ws, (255, 200, 80, 180),
                               (warn_r+5, warn_r+5), warn_r, max(2, int(4*z)))
            screen.blit(ws, (sx-warn_r-5, sy-warn_r-5))


class Schrödinger(Player):
    WEIGHT = 96
    KB_GROWTH = 78
    BASE_KB = 30
    WALK_SPEED = 6.2
    JUMP_POWER = -15.0
    MAX_JUMPS = 2
    ATTACK_DMG = 9
    ATK_FRAMES = 16
    ATK_CD = 26
    HIT_START = 3
    HIT_END = 13

    BODY_COLOR = (155, 60, 220)
    TRIM_COLOR = (90, 20, 140)
    GLOW_COLOR = (210, 130, 255)
    DARK_COLOR = (60, 10, 100)
    DISPLAY_NAME = "Schrödinger"
    DESCRIPTION = (
        "Atom and wave combo fighter.\n"
        "Domain strengthens probability skills."
    )
    PREVIEW_COLOR = (155, 60, 220)
    SKILL_NAME = "Atomic Wave"

    SPRITE_PATH = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Schrödinger/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Schrödinger/attack.png"
    SPRITE_SKILL = "assets/images/charactor/Schrödinger/skill.png"

    SPRITE_SCALE = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Atomic Wave", "ProjectileSkill", 18, 22, 3.5),
        "cc": ("Quantum Collapse Zone", "SummonZoneSkill", 22, 0, 9.0),
        "enhance": ("Superposition Domain", "DomainUltimateSkill", 0, 0, 0.0),
    }

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR
        self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR
        self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"] = AtomicWave()
        self.skills["skill_E"] = QuantumCollapseZone()
        self.skills["skill_R"] = SchrodingerDomain()
        self.skills["skill_Q_domain"] = QuantumPacket()
        self.skills["skill_E_domain"] = ProbabilityStorm()

    def use_skill(self, skill_key: str, event_bus=None, psys=None) -> bool:
        domain_key = skill_key + "_domain"
        if domain_key in self.skills:
            domain_skill = self.skills[domain_key]
            if domain_skill.can_use(self):
                if self.active_skill is not None and self.active_skill is not domain_skill:
                    self.active_skill.on_end(self)
                domain_skill.use(self, event_bus, psys)
                self.active_skill = domain_skill
                return True

        skill = self.skills.get(skill_key)
        if skill and skill.can_use(self):
            if self.active_skill is not None and self.active_skill is not skill:
                self.active_skill.on_end(self)
            skill.use(self, event_bus, psys)
            self.active_skill = skill
            return True

        return False

    def get_char_name(self):
        return "Schrödinger"
