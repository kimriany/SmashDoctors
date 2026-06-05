import pygame
import math
import os
from entities.base_entity import BaseEntity
from systems.skill import Skill


# ── 스프라이트 로더 유틸 ──────────────────────────────────────
def _load_sprite(path: str | None) -> pygame.Surface | None:
    """경로에서 스프라이트를 로드. 없으면 None 반환."""
    if not path:
        return None
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        return img
    except Exception as e:
        print(f"[Player] 스프라이트 로드 실패 ({path}): {e}")
        return None


def _scale_sprite(img: pygame.Surface,
                  w: int, h: int,
                  zoom: float = 1.0) -> pygame.Surface:
    """스프라이트를 히트박스 크기 × zoom 으로 스케일."""
    tw = max(1, int(w * zoom))
    th = max(1, int(h * zoom))
    return pygame.transform.smoothscale(img, (tw, th))


class Player(BaseEntity):
    """기본 캐릭터 (자식 클래스의 베이스)."""

    # ── 스탯 (자식이 override) ────────────────────────────────
    WEIGHT     = 100
    KB_GROWTH  = 80
    BASE_KB    = 30
    WALK_SPEED = 6.5
    JUMP_POWER = -15.5
    MAX_JUMPS  = 2
    ATTACK_DMG = 12
    ATK_FRAMES = 20
    ATK_CD     = 34
    HIT_START  = 4
    HIT_END    = 16

    # ── 색상 (자식이 override) ────────────────────────────────
    BODY_COLOR  = (180, 180, 180)
    TRIM_COLOR  = (100, 100, 100)
    GLOW_COLOR  = (220, 220, 220)
    DARK_COLOR  = ( 60,  60,  60)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 스프라이트 경로 (자식이 override — 없으면 도형 렌더링)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    SPRITE_PATH   = None   # 단일 이미지 (이것만 있어도 됨)
    SPRITE_IDLE   = None   # 상태별 이미지들 (선택)
    SPRITE_JUMP   = None
    SPRITE_ATTACK = None
    SPRITE_SKILL  = None

    # 크기 조정
    SPRITE_SCALE = 1.0
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 0

    # ── 선택창 미리보기 ───────────────────────────────────────
    DISPLAY_NAME  = "Unknown"
    DESCRIPTION   = ""
    PREVIEW_COLOR = (180, 180, 180)
    SKILL_NAME    = "Skill"

    def __init__(self, x: int, y: int, name: str = "Player",
                 player_id: int = 1):
        super().__init__(x, y, 46, 66, name)

        self.player_id = player_id
        self.stocks    = 3
        self.spawn_x   = x
        self.spawn_y   = y

        self.color      = self.BODY_COLOR
        self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR
        self.dark_color = self.DARK_COLOR

        self.skills: dict[str, Skill] = {}
        self._init_skills()

        self.skill_timer   = 0
        self.skill_has_hit = False

        self.respawning    = False
        self.respawn_timer = 0

        self.bob_t  = 0.0
        self.walk_t = 0.0

        #깜빡임 방지
        self.ground_sprite_grace = 0
        self.jump_sprite_lock = 0

        if player_id == 1:
            self.key_left   = pygame.K_a
            self.key_right  = pygame.K_d
            self.key_jump   = pygame.K_w
            self.key_attack = pygame.K_f
            self.key_skill  = pygame.K_g
        else:
            self.key_left   = pygame.K_LEFT
            self.key_right  = pygame.K_RIGHT
            self.key_jump   = pygame.K_UP
            self.key_attack = pygame.K_l
            self.key_skill  = pygame.K_SEMICOLON

        # ── 스프라이트 로드 ──────────────────────────────────
        self._sprites = self._load_sprites()
        self._sprite_cache: dict[tuple, pygame.Surface] = {}

    # ─── 스프라이트 로드 ─────────────────────────────────────────
    def _load_sprites(self) -> dict[str, pygame.Surface | None]:
        """
        클래스 변수에 지정된 경로에서 스프라이트 로드.
        SPRITE_PATH 하나만 있어도 모든 상태에 공유됩니다.
        """
        base = _load_sprite(self.SPRITE_PATH)
        return {
            "idle":   _load_sprite(self.SPRITE_IDLE)   or base,
            "jump":   _load_sprite(self.SPRITE_JUMP)   or base,
            "attack": _load_sprite(self.SPRITE_ATTACK) or base,
            "skill":  _load_sprite(self.SPRITE_SKILL)  or base,
        }

    @property
    def _use_sprite(self) -> bool:
        """스프라이트가 하나라도 로드됐으면 True."""
        return any(v is not None for v in self._sprites.values())

    def _get_sprite(self, state: str, w: int, h: int,
                    zoom: float, flip: bool) -> pygame.Surface | None:
        """상태+크기+방향에 맞는 스케일 스프라이트를 캐시해서 반환."""
        img = self._sprites.get(state)
        if img is None:
            return None
        key = (state, w, h, round(zoom, 2), flip)
        if key not in self._sprite_cache:
            scaled = _scale_sprite(img, w, h, zoom)
            if flip:
                scaled = pygame.transform.flip(scaled, True, False)
            self._sprite_cache[key] = scaled
        return self._sprite_cache[key]

    def _current_state(self) -> str:
        if self.attack_timer > 0:
            return "attack"
        if self.skill_timer > 0:
            return "skill"

        # 점프 버튼을 누른 직후에는 jump 이미지
        if self.jump_sprite_lock > 0:
            return "jump"

        # 진짜로 공중에 있고, y속도도 있을 때만 jump 이미지
        if self.ground_sprite_grace <= 0 and abs(self.vel.y) > 0.25:
            return "jump"

        return "idle"

    # ─── 자식 override ────────────────────────────────────────
    def _init_skills(self):
        self.skills["skill_1"] = Skill(
            name="Burst", damage=28, fatigue_cost=32, cooldown=100
        )

    def get_char_name(self) -> str:
        return self.name

    # ═══════════════════════════════════════════════════════════
    #  입력
    # ═══════════════════════════════════════════════════════════
    def handle_input(self, keys):
        if self.dead or self.respawning:
            return
        moving = False
        if keys[self.key_left]:
            self.vel.x  = -self.WALK_SPEED
            self.facing = -1
            moving      = True
        if keys[self.key_right]:
            self.vel.x  = self.WALK_SPEED
            self.facing = 1
            moving      = True
        if not moving:
            self.vel.x *= 0.74
            if abs(self.vel.x) < 0.25:
                self.vel.x = 0.0

    def handle_keydown(self, key, event_bus, psys=None):
        if self.dead or self.respawning:
            return
        if key == self.key_jump:
            self._jump(psys)
        elif key == self.key_attack:
            self._do_attack(psys)
        elif key == self.key_skill:
            self._do_skill(event_bus, psys)

    def _jump(self, psys):
        if self.jump_count < self.MAX_JUMPS:
            power = self.JUMP_POWER if self.jump_count == 0 \
                    else self.JUMP_POWER * 0.83
            self.vel.y      = power
            self.jump_count += 1

            # 점프 직후 몇 프레임은 확실히 jump 이미지 사용
            self.jump_sprite_lock = 8

            if psys:
                px, py = self._sprite_feet_world()
                psys.spawn_jump(px, py, self.glow_color)

    def _do_attack(self, psys):
        self.start_attack()
        if psys:
            px, py = self._sprite_front_world(y_ratio=0.45, extra=6)
            psys.spawn(px, py, self.glow_color,
                       count=9, speed=5, life=18, r=4)

    def _do_skill(self, event_bus, psys):
        sk = self.skills.get("skill_1")
        if sk and sk.can_use(self.fatigue):
            sk.use()
            self.fatigue       = min(self.max_fatigue,
                                     self.fatigue + sk.fatigue_cost)
            self.skill_timer   = 30
            self.skill_has_hit = False
            event_bus.emit("skill_used", {"user": self, "skill": sk})
            if psys:
                px, py = self._sprite_center_world()
                psys.spawn_skill(px, py, self.glow_color)

    # ═══════════════════════════════════════════════════════════
    #  스킬 히트박스
    # ═══════════════════════════════════════════════════════════
    def get_skill_hitbox(self):
        if not (6 <= self.skill_timer <= 26):
            return None
        w, h = 100, self.rect.h + 10
        ox = self.rect.right - 12 if self.facing == 1 \
             else self.rect.left - w + 12
        return pygame.Rect(ox, self.rect.y - 5, w, h)

    def check_skill_collision(self, target, event_bus, psys=None, fsys=None):
        if self.dead or target.dead or target.invincible > 0:
            return
        sk = self.get_skill_hitbox()
        if sk is None or self.skill_has_hit:
            return
        if sk.colliderect(target.rect):
            self.skill_has_hit = True
            dmg = self.skills["skill_1"].damage
            event_bus.emit("attack_hit", {
                "attacker": self, "target": target,
                "damage": dmg, "is_skill": True,
                "particle_system": psys, "floater_system": fsys,
            })

    # ═══════════════════════════════════════════════════════════
    #  스톡 / 리스폰
    # ═══════════════════════════════════════════════════════════
    def lose_stock(self, event_bus):
        self.stocks    -= 1
        self.damage_pct = 0.0
        self.vel        = pygame.Vector2(0, 0)
        if self.stocks <= 0:
            self.dead = True
            event_bus.emit("entity_dead", {"entity": self})
        else:
            self.respawning    = True
            self.respawn_timer = 100

    def _do_respawn(self, psys):
        self.respawning = False
        self.rect.x     = self.spawn_x
        self.rect.y     = self.spawn_y - 100
        self.vel        = pygame.Vector2(0, 0)
        self.invincible = 130
        if psys:
            px, py = self._sprite_center_world()
            psys.spawn_respawn(px, py, self.glow_color)

    # ═══════════════════════════════════════════════════════════
    #  update
    # ═══════════════════════════════════════════════════════════
    def update(self, dt, platforms, event_bus, psys=None):
        if self.respawning:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self._do_respawn(psys)
            return

        super().update(dt, platforms, event_bus)

        # on_ground가 순간적으로 False가 되는 깜빡임 방지
        if self.on_ground:
            self.ground_sprite_grace = 5
        else:
            self.ground_sprite_grace = max(0, self.ground_sprite_grace - 1)

        # 점프 직후에는 확실히 jump 이미지 유지
        if self.jump_sprite_lock > 0:
            self.jump_sprite_lock -= 1

        for sk in self.skills.values():
            sk.update()
        if self.skill_timer > 0:
            self.skill_timer -= 1
        if self.skill_timer <= 0:
            self.skill_has_hit = False
        self.bob_t  += 0.065
        if abs(self.vel.x) > 0.4:
            self.walk_t += 0.20

    # ═══════════════════════════════════════════════════════════
    #  draw — 이미지 or 도형 자동 분기
    # ═══════════════════════════════════════════════════════════
    def draw(self, screen: pygame.Surface, camera):
        if self.dead:
            return
        if self.respawning:
            self._draw_respawn_ghost(screen)
            return
        if self.invincible > 0 and (self.invincible // 4) % 2 == 1:
            return

        dr  = self._get_draw_rect(camera)
        z   = camera.zoom
        bob = int(math.sin(self.bob_t) * 2.2 * z) if self.on_ground else 0

        if self.on_ground:
            self._draw_shadow(screen, dr)

        if self.skill_timer > 0:
            self._draw_skill_aura(screen, dr, bob, z)

        if self._use_sprite:
            self._draw_sprite(screen, dr, bob, z)
        else:
            self._draw_shape(screen, dr, bob, z)

        if self.skill_timer > 6:
            self._draw_skill_beam(screen, dr, bob, z)

    # ─── 스프라이트 렌더링 ─────────────────────────────────────
    def _draw_sprite(self, screen, dr, bob, z):
        """이미지 스프라이트로 캐릭터 그리기."""
        state = self._current_state()
        flip  = (self.facing == -1)   # 왼쪽을 향할 때 좌우 반전

        img = self._get_sprite(
            state,
            self.rect.w,
            self.rect.h,
            z * self.SPRITE_SCALE,
            flip
        )

        if img is None:
            self._draw_shape(screen, dr, bob, z)
            return

        draw_x = dr.centerx - img.get_width() // 2 + int(self.SPRITE_OFFSET_X * z)
        draw_y = dr.bottom - img.get_height() + int(self.SPRITE_OFFSET_Y * z) + bob

        # 히트 플래시 — 흰색 오버레이
        if self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0:
            flash_img = img.copy()
            flash_img.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(flash_img, (draw_x, draw_y))
        else:
            screen.blit(img, (draw_x, draw_y))

        # 공격 시 주먹 글로우 이펙트 추가
        if self.attack_timer > 0 and self.HIT_START <= self.attack_timer <= self.HIT_END:
            gr = int(38 * z)
            gs = pygame.Surface((gr, gr), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*self.glow_color, 130), (gr//2, gr//2), gr//2)
            if self.facing == 1:
                fist_x = draw_x + img.get_width()
            else:
                fist_x = draw_x - gr

            fist_y = draw_y + int(img.get_height() * 0.45)

            screen.blit(gs, (fist_x - gr // 4, fist_y - gr // 2))

    # ─── 도형 렌더링 (폴백) ────────────────────────────────────
    def _draw_shape(self, screen, dr, bob, z):
        """이미지 없을 때 기존 도형으로 그리기."""
        flash = self._flash_color

        self._draw_legs(screen, dr, bob, z, flash)

        body_r = pygame.Rect(dr.x + int(2*z), dr.y + int(dr.h*0.30) + bob,
                             dr.w - int(4*z), int(dr.h*0.45))
        pygame.draw.rect(screen, flash(self.color), body_r,
                         border_radius=int(7*z))
        pygame.draw.rect(screen, self.trim_color,
                         (body_r.x + int(3*z), body_r.y + int(2*z),
                          int(13*z), body_r.h - int(4*z)),
                         border_radius=int(3*z))
        belt_y = body_r.y + int(body_r.h * 0.72)
        pygame.draw.line(screen, self.dark_color,
                         (body_r.x, belt_y), (body_r.right, belt_y),
                         max(1, int(2*z)))

        head_r = pygame.Rect(dr.x + int(dr.w*0.12),
                             dr.y + int(2*z) + bob,
                             int(dr.w*0.76), int(dr.h*0.32))
        pygame.draw.rect(screen, flash(self.color), head_r,
                         border_radius=int(10*z))
        hair_r = pygame.Rect(head_r.x + int(3*z), head_r.y + int(2*z),
                             head_r.w - int(6*z), int(head_r.h*0.38))
        pygame.draw.rect(screen, self.trim_color, hair_r,
                         border_radius=int(6*z))
        self._draw_glasses(screen, head_r, bob, z)
        self._draw_arms(screen, dr, bob, z, flash)

    # ─── 서브 렌더 메서드들 ────────────────────────────────────
    def _draw_shadow(self, screen, dr):
        sh = pygame.Surface((dr.w - int(8), 9), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 85), sh.get_rect())
        screen.blit(sh, (dr.x + 4, dr.y + dr.h - 3))


    def _draw_skill_aura(self, screen, dr, bob, z):
        t = self.skill_timer / 30.0
        r = int((55 + math.sin(self.bob_t * 4) * 7) * z)
        a = int(90 * t)

        sr = self._sprite_screen_rect(dr, z, bob)

        sf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(sf, (*self.glow_color, a), (r, r), r)
        pygame.draw.circle(sf, (*self.glow_color, a // 2), (r, r), r, int(3 * z))

        screen.blit(sf, (
            sr.centerx - r + int(self.SKILL_AURA_OFFSET_X * z),
            sr.centery - r + int(self.SKILL_AURA_OFFSET_Y * z)
        ))

    def _draw_skill_beam(self, screen, dr, bob, z):
        t = self.skill_timer / 30.0
        bl = int(120 * z)
        bw = max(int(4 * z), int(16 * t * z))
        alp = int(230 * t)

        sr = self._sprite_screen_rect(dr, z, bob)

        # 빔이 나가는 높이. 0.45면 몸통/손 근처.
        beam_y = sr.y + int(sr.h * 0.45)

        if self.facing == 1:
            bx = sr.right - int(6 * z)
        else:
            bx = sr.left - bl + int(6 * z)

        by = beam_y - bw // 2

        bx += int(self.SKILL_BEAM_OFFSET_X * z)
        by += int(self.SKILL_BEAM_OFFSET_Y * z)

        bs = pygame.Surface((bl, bw + int(14 * z)), pygame.SRCALPHA)

        pygame.draw.rect(bs, (*self.glow_color, alp),
                         (0, int(7 * z), bl, bw),
                         border_radius=int(5 * z))

        pygame.draw.rect(bs, (*self.glow_color, alp // 3),
                         (0, int(2 * z), bl, bw + int(10 * z)),
                         border_radius=int(7 * z))

        pygame.draw.rect(bs, (255, 255, 255, int(alp * 0.65)),
                         (0, int(7 * z) + bw // 2 - int(2 * z), bl, int(4 * z)),
                         border_radius=int(5 * z))

        screen.blit(bs, (bx, by - int(7 * z)))

    def _draw_respawn_ghost(self, screen):
        t  = self.respawn_timer / 100.0
        a  = int(180 * t)
        x  = 38 if self.player_id == 1 else screen.get_width() - 148
        sf = pygame.Surface((110, 36), pygame.SRCALPHA)
        sf.fill((0, 0, 0, 100))
        pygame.draw.rect(sf, (*self.glow_color, a), sf.get_rect(), 2,
                         border_radius=6)
        fnt  = pygame.font.SysFont("Arial", 15, bold=True)
        secs = self.respawn_timer // 20 + 1
        txt  = fnt.render(f"{self.name}  ✦{secs}", True, self.glow_color)
        sf.blit(txt, (8, 10))
        screen.blit(sf, (x, 55))


    #위치 조정 메서드
    def _sprite_world_bounds(self):
        """
        화면에 보이는 스프라이트의 월드 좌표 기준 영역.
        ParticleSystem은 월드 좌표를 받으므로 camera.zoom은 절대 넣으면 안 됨.
        """
        scale = getattr(self, "SPRITE_SCALE", 1.0)
        ox = getattr(self, "SPRITE_OFFSET_X", 0)
        oy = getattr(self, "SPRITE_OFFSET_Y", 0)

        w = self.rect.w * scale
        h = self.rect.h * scale

        x = self.rect.centerx - w / 2 + ox
        y = self.rect.bottom - h + oy

        return x, y, w, h

    def _sprite_screen_rect(self, dr, z, bob=0):
        """
        화면에 실제로 그려지는 스프라이트 위치.
        스킬 오라/빔 같은 화면 이펙트 위치 맞출 때 사용.
        """
        scale = getattr(self, "SPRITE_SCALE", 1.0)
        ox = getattr(self, "SPRITE_OFFSET_X", 0)
        oy = getattr(self, "SPRITE_OFFSET_Y", 0)

        w = max(1, int(self.rect.w * z * scale))
        h = max(1, int(self.rect.h * z * scale))

        x = dr.centerx - w // 2 + int(ox * z)
        y = dr.bottom - h + int(oy * z) + bob

        return pygame.Rect(x, y, w, h)

    def _sprite_center_world(self):
        x, y, w, h = self._sprite_world_bounds()
        return x + w / 2, y + h / 2

    def _sprite_feet_world(self):
        """
        스프라이트 발밑 위치.
        점프 파티클, 착지 파티클에 쓰기 좋음.
        """
        ox = getattr(self, "SPRITE_OFFSET_X", 0)
        oy = getattr(self, "SPRITE_OFFSET_Y", 0)
        return self.rect.centerx + ox, self.rect.bottom + oy

    def _sprite_front_world(self, y_ratio=0.45, extra=0):
        """
        캐릭터가 바라보는 앞쪽 위치.
        공격 파티클, 주먹 이펙트에 쓰기 좋음.
        """
        x, y, w, h = self._sprite_world_bounds()

        if self.facing == 1:
            px = x + w + extra
        else:
            px = x - extra

        py = y + h * y_ratio
        return px, py
