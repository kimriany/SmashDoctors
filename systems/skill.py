from systems.font_manager import font
"""
Skill 시스템 — 베이스 클래스 + 6종 스킬 타입

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
스킬 계층 구조
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skill (베이스)
├── BeamSkill          빔형 — 전방 직선 범위
├── ProjectileSkill    투사체 — 날아가는 공/아티팩트
├── SummonZoneSkill    소환 — 경고 후 구역 피해
├── DashSkill          이동기 — 빠른 대시
├── TeleportSkill      순간이동기
└── EnhanceSkill       스탯 강화기

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
각 캐릭터 스킬 구성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
캐릭터는 4개의 슬롯을 가집니다:
    skills["basic"]    기본기  (짧은 쿨, 낮은 피로도)
    skills["cc"]       CC기    (군중제어, 중간 쿨)
    skills["enhance"]  강화기  (버프/이동)
    skills["ult"]      궁극기  (높은 쿨 or 궁극 게이지)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
이미지/이펙트 경로 설정 방법 (각 스킬 클래스에서)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    EFFECT_PATH    = "assets/images/effects/beam_blue.png"   # 이펙트 이미지
    ARTIFACT_PATH  = "assets/images/artifacts/orb_blue.png"  # 투사체/아티팩트 이미지
    ICON_PATH      = "assets/images/icons/skill_beam.png"    # 선택창 아이콘

없으면 자동으로 도형 렌더링으로 폴백합니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import pygame
import math
import os


# ── 이미지 로더 유틸 ─────────────────────────────────────────
def _load_img(path: str | None) -> pygame.Surface | None:
    if not path or not os.path.exists(path):
        return None
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"[Skill] 이미지 로드 실패 ({path}): {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 베이스 스킬
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Skill:
    # ── 스킬 메타 (자식에서 override) ────────────────────────
    SKILL_TYPE   = "base"
    DISPLAY_NAME = "Skill"
    DESCRIPTION  = "A skill."
    COOLDOWN_SEC = 0.0        # 선택창 표시용 (초 단위)

    # ── 이미지 경로 (없으면 도형 렌더링) ─────────────────────
    EFFECT_PATH   = None   # 이펙트 이미지
    ARTIFACT_PATH = None   # 투사체/아티팩트 이미지
    ICON_PATH     = None   # 선택창 아이콘 (48×48 권장)

    def __init__(self, name: str, damage: float,
                 cooldown: int = 0,
                 duration: int = 30):
        self.name         = name
        self.damage       = damage
        self.cooldown     = cooldown        # 프레임 단위
        self.current_cooldown = 0
        self.duration     = duration
        self.timer        = 0
        self.has_hit      = False
        self.charge_value = 1.0
        self.finisher_charge_value = 1.0

        # 이미지 캐시 (첫 사용 시 로드)
        self._effect_img:   pygame.Surface | None = None
        self._artifact_img: pygame.Surface | None = None
        self._icon_img:     pygame.Surface | None = None
        self._images_loaded = False

    def _ensure_images(self):
        if not self._images_loaded:
            self._effect_img   = _load_img(self.EFFECT_PATH)
            self._artifact_img = _load_img(self.ARTIFACT_PATH)
            self._icon_img     = _load_img(self.ICON_PATH)
            self._images_loaded = True

    # ── 상태 ────────────────────────────────────────────────
    @property
    def active(self) -> bool:
        return self.timer > 0

    def has_cooldown(self) -> bool:
        return self.cooldown is not None and self.cooldown > 0

    # ── 발동 조건 ────────────────────────────────────────────
    def can_use(self, owner) -> bool:
        if self.has_cooldown() and self.current_cooldown > 0:
            return False
        return self.can_activate(owner)

    def can_activate(self, owner) -> bool:
        """자식에서 override — 특수 발동 조건."""
        return True

    def get_domain_upgrade_id(self, owner):
        if not getattr(owner, "domain_active", False):
            return None
        upgrades = getattr(owner, "domain_upgrades", {}) or {}
        return upgrades.get(self.SKILL_TYPE)

    # ── 사용 ────────────────────────────────────────────────
    def use(self, owner, event_bus=None, psys=None):
        if self.has_cooldown():
            self.current_cooldown = self.cooldown
        self.timer   = self.duration
        self.has_hit = False
        self.on_start(owner, event_bus, psys)

    # ── 업데이트 ─────────────────────────────────────────────
    def update_cooldown(self):
        if self.has_cooldown() and self.current_cooldown > 0:
            self.current_cooldown -= 1

    def update_active(self, owner, event_bus=None, psys=None):
        if self.timer > 0:
            self.on_update(owner, event_bus, psys)
            self.timer -= 1

    # ── 히트 처리 ────────────────────────────────────────────
    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        if self.has_hit:
            return
        self.has_hit = True
        event_bus.emit("attack_hit", {
            "attacker": owner,
            "target": target,
            "damage": self.damage,
            "is_skill": True,
            "skill": self,
            "charge_value": self.charge_value,
            "finisher_charge_value": self.finisher_charge_value,
            "particle_system": psys,
            "floater_system": fsys,
        })

    # ── 히트박스 ─────────────────────────────────────────────
    def get_hitbox(self, owner) -> pygame.Rect | None:
        """자식에서 override."""
        return None



    # ── 이벤트 훅 (자식 override) ────────────────────────────
    def on_start(self, owner, event_bus=None, psys=None):   pass
    def on_update(self, owner, event_bus=None, psys=None):  pass

    # ── 렌더링 (자식 override) ───────────────────────────────
    def draw_behind(self, owner, screen, camera, dr, bob, z): pass
    def draw_front(self, owner, screen, camera, dr, bob, z):  pass

    # ── 선택창 아이콘 그리기 ─────────────────────────────────
    def draw_icon(self, screen: pygame.Surface,
                  x: int, y: int, size: int = 48):
        """
        캐릭터 선택창 스킬 아이콘.
        ICON_PATH 이미지가 있으면 표시, 없으면 도형으로 폴백.
        """
        self._ensure_images()
        if self._icon_img is not None:
            scaled = pygame.transform.smoothscale(self._icon_img, (size, size))
            screen.blit(scaled, (x, y))
        else:
            self._draw_default_icon(screen, x, y, size)

    def _draw_default_icon(self, screen, x, y, size):
        """아이콘 이미지 없을 때 기본 도형 아이콘."""
        cx, cy = x + size//2, y + size//2
        pygame.draw.rect(screen, (40, 40, 60),
                         (x, y, size, size), border_radius=8)
        pygame.draw.rect(screen, (80, 80, 120),
                         (x, y, size, size), 1, border_radius=8)
        # 스킬 타입별 기본 모양
        self._draw_type_icon(screen, cx, cy, size)

    def _draw_type_icon(self, screen, cx, cy, size):
        r = size // 3
        pygame.draw.circle(screen, (100, 100, 180), (cx, cy), r)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BeamSkill — 전방 직선 빔
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class BeamSkill(Skill):
    SKILL_TYPE   = "beam"
    DISPLAY_NAME = "Beam"
    DESCRIPTION  = "Fires a beam in front."

    # 빔 설정 (자식 override)
    BEAM_LENGTH  = 280   # 월드 픽셀
    BEAM_WIDTH   = 28
    BEAM_COLOR   = (100, 180, 255)
    BEAM_GLOW    = (160, 220, 255)

    def get_hitbox(self, owner) -> pygame.Rect | None:
        if not self.active:
            return None
        w = self.BEAM_LENGTH
        h = self.BEAM_WIDTH + 14
        ox = owner.rect.right - 6 if owner.facing == 1 \
             else owner.rect.left - w + 6
        return pygame.Rect(ox, owner.rect.centery - h//2, w, h)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        self._ensure_images()
        t     = self.timer / self.duration
        alpha = int(230 * t)
        blen  = int(self.BEAM_LENGTH * z)
        bw    = max(int(4*z), int(self.BEAM_WIDTH * t * z))

        if self._effect_img is not None:
            # 이미지 이펙트
            scaled = pygame.transform.smoothscale(
                self._effect_img, (blen, bw + int(14*z)))
            if owner.facing == -1:
                scaled = pygame.transform.flip(scaled, True, False)
            scaled.set_alpha(alpha)
            bx = dr.right - int(6*z) if owner.facing == 1 \
                 else dr.left - blen + int(6*z)
            screen.blit(scaled, (bx, dr.centery + bob - bw//2 - int(7*z)))
        else:
            # 도형 렌더링
            bx = dr.right - int(6*z) if owner.facing == 1 \
                 else dr.left - blen + int(6*z)
            by = dr.centery + bob - bw//2
            bs = pygame.Surface((blen, bw + int(14*z)), pygame.SRCALPHA)
            pygame.draw.rect(bs, (*self.BEAM_COLOR, alpha),
                             (0, int(7*z), blen, bw), border_radius=int(5*z))
            pygame.draw.rect(bs, (*self.BEAM_GLOW, alpha//3),
                             (0, int(2*z), blen, bw+int(10*z)), border_radius=int(7*z))
            pygame.draw.rect(bs, (255,255,255,int(alpha*0.6)),
                             (0, int(7*z)+bw//2-int(2*z), blen, int(4*z)),
                             border_radius=int(5*z))
            screen.blit(bs, (bx, by - int(7*z)))

    def _draw_type_icon(self, screen, cx, cy, size):
        s = size // 3
        pygame.draw.line(screen, (100, 180, 255),
                         (cx - s, cy), (cx + s, cy), max(2, size//8))
        pygame.draw.circle(screen, (160, 220, 255), (cx + s, cy), size//10)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ProjectileSkill — 날아가는 투사체
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ProjectileSkill(Skill):
    SKILL_TYPE   = "projectile"
    DISPLAY_NAME = "Projectile"
    DESCRIPTION  = "Launches a projectile forward."

    PROJ_SPEED  = 9.0    # 월드 픽셀/프레임
    PROJ_SIZE   = 18     # 반지름
    PROJ_COLOR  = (255, 200, 80)
    PROJ_GLOW   = (255, 240, 160)

    def on_start(self, owner, event_bus=None, psys=None):
        # 투사체 상태 초기화
        self._px    = float(owner.rect.centerx)
        self._py    = float(owner.rect.centery)
        self._vx    = self.PROJ_SPEED * owner.facing
        self._alive = True

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive:
            return
        self._px += self._vx
        # 화면 밖 제거
        if abs(self._px - owner.rect.centerx) > 800:
            self._alive = False

    def get_hitbox(self, owner) -> pygame.Rect | None:
        if not self.active or not getattr(self, '_alive', False):
            return None
        r = self.PROJ_SIZE
        return pygame.Rect(int(self._px) - r, int(self._py) - r, r*2, r*2)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active or not getattr(self, '_alive', False):
            return
        self._ensure_images()
        sx, sy = camera.world_to_screen(self._px, self._py)
        r = max(4, int(self.PROJ_SIZE * z))

        if self._artifact_img is not None:
            scaled = pygame.transform.smoothscale(
                self._artifact_img, (r*2, r*2))
            screen.blit(scaled, (sx - r, sy - r))
        else:
            # 글로우 원
            gs = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*self.PROJ_GLOW, 80), (r*2, r*2), r*2)
            pygame.draw.circle(gs, (*self.PROJ_COLOR, 200), (r*2, r*2), r)
            pygame.draw.circle(gs, (255, 255, 255, 180), (r*2, r*2), r//3)
            screen.blit(gs, (sx - r*2, sy - r*2))

    def _draw_type_icon(self, screen, cx, cy, size):
        r = size // 5
        pygame.draw.circle(screen, (255, 200, 80), (cx, cy), r)
        pygame.draw.circle(screen, (255, 240, 160), (cx, cy), r, 2)
        # 궤적
        pygame.draw.line(screen, (255, 200, 80, 120),
                         (cx - size//3, cy), (cx - r, cy), max(1, size//12))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SummonZoneSkill — 경고 후 구역 소환
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SummonZoneSkill(Skill):
    SKILL_TYPE   = "summon_zone"
    DISPLAY_NAME = "Summon Zone"
    DESCRIPTION  = "Warns, then summons a damage zone."

    WARN_FRAMES  = 40    # 경고 표시 시간 (duration 앞부분)
    ZONE_W       = 120
    ZONE_H       = 80
    ZONE_COLOR   = (220, 80, 80)
    ZONE_GLOW    = (255, 140, 100)

    def on_start(self, owner, event_bus=None, psys=None):
        # 타깃 위치 = 상대방 발밑 (owner가 facing하는 방향 앞)
        offset = 200 * owner.facing
        self._zone_x = owner.rect.centerx + offset
        self._zone_y = owner.rect.bottom   # 바닥 기준

    def get_hitbox(self, owner) -> pygame.Rect | None:
        if not self.active:
            return None
        # WARN_FRAMES 이후에만 판정 활성
        if self.timer > self.duration - self.WARN_FRAMES:
            return None
        zx = getattr(self, '_zone_x', owner.rect.centerx)
        zy = getattr(self, '_zone_y', owner.rect.bottom)
        return pygame.Rect(zx - self.ZONE_W//2, zy - self.ZONE_H,
                           self.ZONE_W, self.ZONE_H)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        self._ensure_images()
        zx = getattr(self, '_zone_x', owner.rect.centerx)
        zy = getattr(self, '_zone_y', owner.rect.bottom)
        sx, sy = camera.world_to_screen(zx, zy)
        zw = int(self.ZONE_W * z)
        zh = int(self.ZONE_H * z)

        t_ratio = self.timer / self.duration
        warn    = self.timer > self.duration - self.WARN_FRAMES
        alpha   = int(160 * t_ratio) if not warn else \
                  int(80 + 80 * abs(math.sin(self.timer * 0.4)))

        if self._effect_img is not None:
            scaled = pygame.transform.smoothscale(self._effect_img, (zw, zh))
            scaled.set_alpha(alpha)
            screen.blit(scaled, (sx - zw//2, sy - zh))
        else:
            sf = pygame.Surface((zw, zh), pygame.SRCALPHA)
            col = self.ZONE_COLOR if not warn else (255, 255, 100)
            pygame.draw.rect(sf, (*col, alpha//2), (0, 0, zw, zh), border_radius=6)
            pygame.draw.rect(sf, (*col, alpha),    (0, 0, zw, zh), 2, border_radius=6)
            if warn:
                ex_sf = font(int(18*z), bold=True).render(
                    "!", True, (255, 80, 80))
                sf.blit(ex_sf, (zw//2 - ex_sf.get_width()//2,
                                zh//2 - ex_sf.get_height()//2))
            screen.blit(sf, (sx - zw//2, sy - zh))

    def _draw_type_icon(self, screen, cx, cy, size):
        s = size // 3
        pygame.draw.rect(screen, (220, 80, 80),
                         (cx - s, cy - s//2, s*2, s), border_radius=4)
        pygame.draw.rect(screen, (255, 140, 100),
                         (cx - s, cy - s//2, s*2, s), 1, border_radius=4)
        fnt = font(max(8, size//5), bold=True)
        ex  = fnt.render("!", True, (255, 255, 100))
        screen.blit(ex, (cx - ex.get_width()//2, cy - ex.get_height()//2 - s//4))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DashSkill — 빠른 이동기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DashSkill(Skill):
    SKILL_TYPE   = "dash"
    DISPLAY_NAME = "Dash"
    DESCRIPTION  = "Dashes quickly in facing direction."

    DASH_SPEED   = 18.0   # 프레임당 속도
    DASH_FRAMES  = 8      # duration 중 실제 이동 프레임
    DASH_DAMAGE  = 0      # 대시 자체 데미지 (0이면 무적만)
    TRAIL_COLOR  = (150, 200, 255)

    def on_start(self, owner, event_bus=None, psys=None):
        owner.vel.x      = self.DASH_SPEED * owner.facing
        owner.vel.y      = 0
        owner.invincible = self.DASH_FRAMES + 4

    def on_update(self, owner, event_bus=None, psys=None):
        if self.timer > self.duration - self.DASH_FRAMES:
            owner.vel.x = self.DASH_SPEED * owner.facing

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        t     = self.timer / self.duration
        alpha = int(120 * t)
        for i in range(3):
            offset = int((i + 1) * 18 * z * -owner.facing)
            trail  = pygame.Surface((dr.w, dr.h), pygame.SRCALPHA)
            pygame.draw.rect(trail, (*self.TRAIL_COLOR, alpha // (i+1)),
                             (0, 0, dr.w, dr.h), border_radius=6)
            screen.blit(trail, (dr.x + offset, dr.y + bob))

    def _draw_type_icon(self, screen, cx, cy, size):
        s = size // 3
        for i in range(3):
            a = 200 - i * 60
            pygame.draw.line(screen, (*self.TRAIL_COLOR, a) if len(self.TRAIL_COLOR)==3
                             else self.TRAIL_COLOR,
                             (cx - s + i*s//2, cy - s//3),
                             (cx + s//2 + i*s//2, cy + s//3),
                             max(1, size//14))
        pygame.draw.polygon(screen, (200, 230, 255),
                            [(cx + s, cy), (cx, cy - s//3), (cx, cy + s//3)])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TeleportSkill — 순간이동
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TeleportSkill(Skill):
    SKILL_TYPE   = "teleport"
    DISPLAY_NAME = "Teleport"
    DESCRIPTION  = "Teleports behind the opponent."

    TELEPORT_OFFSET = 80   # 상대 뒤 거리 (월드 픽셀)
    FLASH_COLOR     = (200, 160, 255)

    def on_start(self, owner, event_bus=None, psys=None):
        # target이 owner.target 속성에 있으면 그 뒤로 순간이동
        target = getattr(owner, '_skill_target', None)
        if target and not target.dead:
            tx = target.rect.centerx
            # 상대 facing 반대쪽으로 등장
            side   = -target.facing
            dest_x = tx + side * self.TELEPORT_OFFSET
            dest_y = target.rect.y
            owner.rect.x = int(dest_x - owner.rect.w // 2)
            owner.rect.y = int(dest_y)
            owner.facing = -side
        owner.vel          = pygame.Vector2(0, 0)
        owner.invincible   = 20
        if psys:
            psys.spawn_skill(owner.rect.centerx, owner.rect.centery,
                             self.FLASH_COLOR)

    def _draw_type_icon(self, screen, cx, cy, size):
        s = size // 3
        # 출발점 (흐릿)
        pygame.draw.circle(screen, (120, 80, 200), (cx - s, cy), size//8)
        # 도착점 (밝음)
        pygame.draw.circle(screen, (200, 160, 255), (cx + s, cy), size//7)
        # 화살표
        pygame.draw.line(screen, (180, 140, 240),
                         (cx - s + size//8, cy), (cx + s - size//8, cy),
                         max(1, size//14))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EnhanceSkill — 스탯 강화기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EnhanceSkill(Skill):
    SKILL_TYPE   = "enhance"
    DISPLAY_NAME = "Enhance"
    DESCRIPTION  = "Temporarily boosts stats."

    SPEED_MULT   = 1.5    # 이동속도 배율
    DMG_BONUS    = 5      # 공격 데미지 추가
    ENHANCE_COLOR = (255, 220, 60)

    def on_start(self, owner, event_bus=None, psys=None):
        # 원래 스탯 저장 후 강화 적용
        self._orig_speed  = getattr(owner, 'WALK_SPEED', 6.5)
        self._orig_dmg    = owner.ATTACK_DMG
        # 런타임 속도는 player.handle_input에서 읽으므로 인스턴스 속성으로 override
        owner._speed_override = self._orig_speed * self.SPEED_MULT
        owner._dmg_override   = self._orig_dmg + self.DMG_BONUS
        if psys:
            psys.spawn_skill(owner.rect.centerx, owner.rect.centery,
                             self.ENHANCE_COLOR)

    def on_update(self, owner, event_bus=None, psys=None):
        # 강화 효과 유지 (파티클 스파크)
        if self.timer % 8 == 0 and psys:
            psys.spawn(owner.rect.centerx, owner.rect.centery,
                       self.ENHANCE_COLOR, count=3, speed=2, life=12, r=3)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        t  = self.timer / self.duration
        r  = int((40 + math.sin(owner.bob_t * 4) * 6) * z)
        a  = int(70 * t)
        sf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(sf, (*self.ENHANCE_COLOR, a), (r, r), r)
        screen.blit(sf, (dr.centerx - r, dr.centery - r + bob))

    def on_end(self, owner):
        """강화 해제 — Player.update()에서 timer==0 감지 후 호출."""
        if hasattr(owner, '_speed_override'):
            del owner._speed_override
        if hasattr(owner, '_dmg_override'):
            del owner._dmg_override

    def _draw_type_icon(self, screen, cx, cy, size):
        s = size // 3
        # 위를 향한 화살표
        pygame.draw.polygon(screen, (255, 220, 60),
                            [(cx, cy - s), (cx - s//2, cy), (cx + s//2, cy)])
        pygame.draw.rect(screen, (255, 200, 40),
                         (cx - s//4, cy, s//2, s//2), border_radius=2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UltimateSkill — 궁극기 베이스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UltimateSkill(Skill):
    SKILL_TYPE   = "ultimate"
    DISPLAY_NAME = "Ultimate"
    DESCRIPTION  = "Requires 100 ultimate gauge."

    def __init__(self, name, damage,  duration=60):
        super().__init__(name=name, damage=damage,
                         cooldown=None, duration=duration)

    def can_activate(self, owner) -> bool:
        return getattr(owner, "ultimate_gauge", 0) >= 100

    def use(self, owner, event_bus=None, psys=None):
        owner.ultimate_gauge = 0
        self.timer   = self.duration
        self.has_hit = False
        self.on_start(owner, event_bus, psys)

    def _draw_type_icon(self, screen, cx, cy, size):
        r = size // 3
        pygame.draw.circle(screen, (255, 180, 40), (cx, cy), r)
        pygame.draw.circle(screen, (255, 240, 120), (cx, cy), r, 2)
        fnt = font(max(8, size//5), bold=True)
        ult = fnt.render("U", True, (255, 255, 200))
        screen.blit(ult, (cx - ult.get_width()//2,
                          cy - ult.get_height()//2))

class DomainUltimateSkill(UltimateSkill):
    """
    영역 전개형 궁극기 베이스 클래스.

    실제 연출은 DomainSystem이 담당한다.
    이 스킬은 domain_request 이벤트만 보낸다.
    """

    DOMAIN_BG_PATH = None

    # 스킬별 경계 파티클 색상
    DOMAIN_PARTICLE_COLOR = (0, 0, 0)

    # 몇 대 맞으면 영역이 깨지는지
    BREAK_HITS = 5

    # 카메라 워킹 설정
    # 작을수록 빠름
    CUTSCENE_FRAMES = 34
    CUTSCENE_ZOOM = 1.45

    # 배경 전환 속도
    # 클수록 빠름
    TRANSITION_SPEED = 0.045

    # 배경 전환 중에도 게임을 멈출지
    FREEZE_DURING_TRANSITION = True

    DISPLAY_NAME = "Domain Expansion"
    DESCRIPTION = "Open a special domain."

    def __init__(self, name="Domain Expansion", damage=0, duration=999999):
        super().__init__(
            name=name,
            damage=damage,
            duration=duration,
        )

    def can_activate(self, owner):
        if getattr(owner, "domain_active", False):
            return False
        if getattr(owner, "domain_locked", False):
            return False
        return getattr(owner, "domain_charge_stack", 0.0) >= getattr(owner, "domain_charge_required", 8.0)

    def on_start(self, owner, event_bus=None, psys=None):
        if event_bus:
            event_bus.emit("domain_request", {
                "owner": owner,
                "skill": self,

                "bg_path": self.DOMAIN_BG_PATH,
                "particle_color": self.DOMAIN_PARTICLE_COLOR,

                "break_hits": self.BREAK_HITS,

                "cutscene_frames": self.CUTSCENE_FRAMES,
                "cutscene_zoom": self.CUTSCENE_ZOOM,

                "transition_speed": self.TRANSITION_SPEED,
                "freeze_during_transition": self.FREEZE_DURING_TRANSITION,
            })
