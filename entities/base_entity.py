"""
BaseEntity — 모든 전투 캐릭터의 부모 클래스.

HP 없음. damage_pct(%) 누적 → 넉백 증가 (스매시 브라더스 공식 적용).
실점은 blast zone 이탈로만 발생.

자식 클래스가 반드시 override해야 하는 메서드:
    draw(screen, camera)         — 캐릭터 외형
    get_char_name() -> str       — 캐릭터 이름
    get_passive_effect()         — 캐릭터 고유 효과 (선택)

참고 넉백 공식 (Smash Ultimate 기반):
    KB = (((p/10 + p*d/20) * (200/(w+100)) * 1.4) + 18) * (s/100) + b
    p = 피격자 현재 %, d = 공격 데미지, w = 피격자 무게
    s = 넉백 성장, b = 기본 넉백
"""
import pygame
import math
from settings import GRAVITY, MAX_FALL_SPEED


class BaseEntity:
    # 기본 물리 상수 (자식 클래스에서 오버라이드 가능)
    WEIGHT       = 100    # 무게 (높을수록 덜 날아감)
    KB_GROWTH    = 80     # 넉백 성장 (s)
    BASE_KB      = 30     # 기본 넉백 (b)
    WALK_SPEED   = 6.5
    JUMP_POWER   = -15.5
    MAX_JUMPS    = 2
    ATTACK_DMG   = 12
    ATK_FRAMES   = 20    # 공격 총 프레임
    ATK_CD       = 34
    HIT_START    = 4     # 히트박스 활성화 시작 프레임
    HIT_END      = 16    # 히트박스 활성화 종료 프레임

    def __init__(self, x: int, y: int, w: int, h: int, name: str = "Entity"):
        self.name = name
        self.rect = pygame.Rect(x, y, w, h)
        self.vel  = pygame.Vector2(0, 0)
        self.dead = False

        self.on_ground  = False
        self.facing     = 1        # 1=오른쪽, -1=왼쪽

        # ── 데미지 (HP 없음) ──
        self.damage_pct  = 0.0    # 누적 % (이게 높을수록 넉백↑)

        # ── 피로도 ──
        self.fatigue     = 0.0
        self.max_fatigue = 100.0

        # ── 공격 상태 ──
        self.attack_timer    = 0
        self.attack_cooldown = 0
        self.has_hit         = False

        # ── 방어/무적 ──
        self.invincible  = 0

        # ── 시각 ──
        self.hit_flash   = 0
        self.shake_x     = 0.0
        self.shake_y     = 0.0

        # 착지 스쿼시
        self.land_squash     = 0.0
        self._was_on_ground  = False

        # 공중 상태
        self.jump_count  = 0
        self.is_launched = False   # 넉백 날아가는 중

    # ═══════════════════════════════════════════════════════════
    #  자식 클래스 override 대상
    # ═══════════════════════════════════════════════════════════
    def draw(self, screen: pygame.Surface, camera):
        """외형 렌더링 — 자식에서 반드시 구현."""
        raise NotImplementedError

    def get_char_name(self) -> str:
        return self.name

    # ═══════════════════════════════════════════════════════════
    #  물리
    # ═══════════════════════════════════════════════════════════
    def apply_gravity(self):
        self.vel.y = min(self.vel.y + GRAVITY, MAX_FALL_SPEED)

    def move_and_collide(self, platforms: list[pygame.Rect]):
        # X 이동
        self.rect.x += int(self.vel.x)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel.x > 0: self.rect.right = p.left
                else:              self.rect.left  = p.right
                self.vel.x = 0

        # Y 이동
        self._was_on_ground = self.on_ground
        self.on_ground = False
        self.rect.y   += int(self.vel.y)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel.y > 0:
                    self.rect.bottom = p.top
                    self.vel.y       = 0
                    self.on_ground   = True
                    self.jump_count  = 0
                    self.is_launched = False
                elif self.vel.y < 0:
                    self.rect.top = p.bottom
                    self.vel.y    = 0

    # ═══════════════════════════════════════════════════════════
    #  공격
    # ═══════════════════════════════════════════════════════════
    def start_attack(self):
        if self.attack_cooldown <= 0:
            self.attack_timer    = self.ATK_FRAMES
            self.attack_cooldown = self.ATK_CD
            self.has_hit         = False

    def get_attack_hitbox(self) -> pygame.Rect | None:
        if not (self.HIT_START <= self.attack_timer <= self.HIT_END):
            return None
        w, h = 60, 42
        ox = self.rect.right if self.facing == 1 else self.rect.left - w
        return pygame.Rect(ox, self.rect.y + 10, w, h)

    def check_attack_collision(self, target: "BaseEntity", event_bus,
                               psys=None, fsys=None):
        if self.dead or target.dead or target.invincible > 0:
            return
        hb = self.get_attack_hitbox()
        if hb is None or self.has_hit:
            return
        if hb.colliderect(target.rect):
            self.has_hit = True
            event_bus.emit("attack_hit", {
                "attacker": self, "target": target,
                "damage": self.ATTACK_DMG,
                "is_skill": False,
                "particle_system": psys,
                "floater_system": fsys,
            })

    # ═══════════════════════════════════════════════════════════
    #  피격 & 넉백
    # ═══════════════════════════════════════════════════════════
    def take_damage(self, damage: float):
        """HP 없음 — damage_pct 누적만."""
        if self.invincible > 0:
            return
        self.damage_pct += damage
        self.hit_flash   = 18
        self.invincible  = 24

    def apply_knockback(self, attacker: "BaseEntity", damage: float,
                        camera=None):
        """
        넉백 공식 (Smash Ultimate 기반, 스케일 대폭 상향)

        기본 공식:
            raw = (((p/10 + p*d/20) * (200/(w+100)) * 1.4) + 18) * (s/100) + b

        조정 사항:
            1. 스케일 계수 0.026 → 0.072  (약 2.8배 상향)
            2. 최대 클램프 28 → 55
            3. 피로도 페널티: fatigue 100% 시 넉백 +60%
            4. 넉백 저항(_kb_resist) 지원
        """
        p = self.damage_pct
        d = damage
        w = getattr(self, "WEIGHT",    100)
        s = getattr(self, "KB_GROWTH",  80)
        b = getattr(self, "BASE_KB",    30)

        # 기본 넉백 계산
        raw = (((p / 10.0 + p * d / 20.0) * (200.0 / (w + 100.0)) * 1.4)
               + 18.0) * (s / 100.0) + b

        # ── 스케일 (크게 올림) ──────────────────────────────
        # 기본 타격: 데미지 누적에 따라 점점 날아가는 느낌
        speed = raw * 0.32

        # ── 피로도 페널티 ────────────────────────────────────
        # fatigue 0% → ×1.0  /  fatigue 100% → ×2.0
        # 피로도 꽉 찬 상태에서 맞으면 2배로 날아감
        fatigue_ratio   = self.fatigue / max(self.max_fatigue, 1.0)
        fatigue_penalty = 1.0 + fatigue_ratio * 1.0
        speed *= fatigue_penalty

        # ── 넉백 저항 ────────────────────────────────────────
        resist = getattr(self, "_kb_resist", 0.0)
        speed *= (1.0 - resist)

        # ── 클램프 ───────────────────────────────────────────
        # 최솟값을 높여 약한 공격도 확실히 밀림
        speed = max(6.0, min(speed, 120.0))

        dir_x      = 1 if attacker.rect.centerx < self.rect.centerx else -1
        vel_x      = dir_x * speed * 1.8          # 좌우 강화
        vel_y      = -(speed * 0.20)               # 위 억제
        # vel.x 최종 클램프 (배율 적용 후)
        MAX_VEL_X  = 90.0
        vel_x      = max(-MAX_VEL_X, min(MAX_VEL_X, vel_x))
        self.vel.x = vel_x
        self.vel.y = vel_y
        self.shake_x = dir_x * min(18, int(abs(vel_x) * 0.3))
        self.shake_y = -min(6, int(speed * 0.15))
        self.is_launched = True

        # Special Zoom 트리거
        if camera is not None and hasattr(camera, "SZOOM_THRESHOLD"):
            if speed >= camera.SZOOM_THRESHOLD:
                camera.trigger_special_zoom(self.rect.centerx, self.rect.centery)

    # ═══════════════════════════════════════════════════════════
    #  update (공통)
    # ═══════════════════════════════════════════════════════════
    def update(self, dt: float, platforms: list, event_bus):
        if self.dead:
            return

        self.apply_gravity()
        self.move_and_collide(platforms)

        # 착지 감지 → 스쿼시
        if self.on_ground and not self._was_on_ground:
            self.land_squash = 1.0

        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.attack_timer    > 0: self.attack_timer    -= 1
        if self.attack_timer   <= 0: self.has_hit          = False
        if self.invincible      > 0: self.invincible       -= 1
        if self.hit_flash       > 0: self.hit_flash        -= 1

        # 피로도 자연 회복
        if self.fatigue > 0:
            self.fatigue = max(0.0, self.fatigue - 0.30)

        # 착지 스쿼시 감쇠
        if self.land_squash > 0:
            self.land_squash = max(0.0, self.land_squash - 0.11)

        self.shake_x *= 0.68
        self.shake_y *= 0.68

    # ═══════════════════════════════════════════════════════════
    #  렌더링 헬퍼
    # ═══════════════════════════════════════════════════════════
    def _get_draw_rect(self, camera) -> pygame.Rect:
        """카메라 변환 + 쉐이크 + 스쿼시/스트레치 적용."""
        base = camera.apply_rect(self.rect)

        # 쉐이크
        base.x += int(self.shake_x * camera.zoom)
        base.y += int(self.shake_y * camera.zoom)

        # 스쿼시/스트레치
        sq = self.land_squash
        if sq > 0:
            dw = int(base.w * (1.0 + sq * 0.20))
            dh = int(base.h * (1.0 - sq * 0.28))
            base.x -= (dw - base.w) // 2
            base.y += (base.h - dh)
            base.w = dw
            base.h = dh

        return base

    def _flash_color(self, normal: tuple) -> tuple:
        """히트 플래시 중이면 흰색 반환."""
        if self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0:
            return (255, 255, 255)
        return normal
