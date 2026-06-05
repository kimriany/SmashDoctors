"""
Player 클래스 — BaseEntity 자식.
캐릭터별 외형/능력치는 이 클래스를 상속해서 구현.

입력 처리, 스킬, 스톡, 리스폰은 여기에 모두 있음.
draw()는 기본 구현 제공 + 자식이 override 가능.
"""
import pygame
import math
from entities.base_entity import BaseEntity
from systems.skill import Skill


class Player(BaseEntity):
    """기본 캐릭터 (자식 클래스의 베이스)."""

    # ── 자식이 오버라이드할 스탯 ──
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

    # 캐릭터 기본 색상 (자식이 override)
    BODY_COLOR  = (180, 180, 180)
    TRIM_COLOR  = (100, 100, 100)
    GLOW_COLOR  = (220, 220, 220)
    DARK_COLOR  = (60,  60,  60)

    def __init__(self, x: int, y: int, name: str = "Player",
                 player_id: int = 1):
        super().__init__(x, y, 46, 66, name)

        self.player_id = player_id
        self.stocks    = 3
        self.spawn_x   = x
        self.spawn_y   = y

        # 색상 (자식의 클래스 변수 사용)
        self.color      = self.BODY_COLOR
        self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR
        self.dark_color = self.DARK_COLOR

        # 스킬 (자식이 _init_skills 에서 설정)
        self.skills: dict[str, Skill] = {}
        self._init_skills()

        self.skill_timer   = 0
        self.skill_has_hit = False

        # 리스폰
        self.respawning    = False
        self.respawn_timer = 0

        # 애니메이션
        self.bob_t   = 0.0
        self.walk_t  = 0.0

        # 키 매핑
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

    # ── 자식이 오버라이드 ──────────────────────────────────────
    def _init_skills(self):
        """스킬 등록. 자식 클래스에서 override."""
        self.skills["skill_1"] = Skill(
            name="Burst", damage=28, fatigue_cost=32, cooldown=100
        )

    def get_char_name(self) -> str:
        return self.name

    # ═══════════════════════════════════════════════════════════
    #  입력
    # ═══════════════════════════════════════════════════════════
    def handle_input(self, keys: pygame.key.ScancodeWrapper):
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

    def handle_keydown(self, key: int, event_bus, psys=None, camera=None):
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
            power           = self.JUMP_POWER if self.jump_count == 0 \
                              else self.JUMP_POWER * 0.83
            self.vel.y      = power
            self.jump_count += 1
            if psys:
                psys.spawn_jump(self.rect.centerx, self.rect.bottom,
                                self.glow_color)

    def _do_attack(self, psys):
        self.start_attack()
        if psys:
            ox = self.rect.right if self.facing == 1 else self.rect.left - 20
            psys.spawn(ox, self.rect.centery, self.glow_color,
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
                psys.spawn_skill(self.rect.centerx, self.rect.centery,
                                 self.glow_color)

    # ═══════════════════════════════════════════════════════════
    #  스킬 히트박스
    # ═══════════════════════════════════════════════════════════
    def get_skill_hitbox(self) -> pygame.Rect | None:
        if not (6 <= self.skill_timer <= 26):
            return None
        w, h = 100, self.rect.h + 10
        ox = self.rect.right - 12 if self.facing == 1 \
             else self.rect.left - w + 12
        return pygame.Rect(ox, self.rect.y - 5, w, h)

    def check_skill_collision(self, target: BaseEntity, event_bus,
                               psys=None, fsys=None):
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
        self.stocks     -= 1
        self.damage_pct  = 0.0
        self.vel         = pygame.Vector2(0, 0)
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
            psys.spawn_respawn(self.rect.centerx, self.rect.centery,
                               self.glow_color)

    # ═══════════════════════════════════════════════════════════
    #  update
    # ═══════════════════════════════════════════════════════════
    def update(self, dt: float, platforms: list, event_bus, psys=None):
        if self.respawning:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self._do_respawn(psys)
            return

        super().update(dt, platforms, event_bus)

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
    #  렌더링 (기본 구현 — 자식이 override 가능)
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

        # 그림자
        if self.on_ground:
            self._draw_shadow(screen, dr)

        # 스킬 오라
        if self.skill_timer > 0:
            self._draw_skill_aura(screen, dr, bob, z)

        flash = self._flash_color

        # 다리
        self._draw_legs(screen, dr, bob, z, flash)

        # 몸통
        body_r = pygame.Rect(dr.x + int(2*z), dr.y + int(dr.h*0.30) + bob,
                             dr.w - int(4*z), int(dr.h*0.45))
        pygame.draw.rect(screen, flash(self.color), body_r,
                         border_radius=int(7*z))

        # 가운 라펠
        pygame.draw.rect(screen, self.trim_color,
                         (body_r.x + int(3*z), body_r.y + int(2*z),
                          int(13*z), body_r.h - int(4*z)),
                         border_radius=int(3*z))

        # 벨트 라인
        belt_y = body_r.y + int(body_r.h * 0.72)
        pygame.draw.line(screen, self.dark_color,
                         (body_r.x, belt_y), (body_r.right, belt_y),
                         max(1, int(2*z)))

        # 머리
        head_r = pygame.Rect(dr.x + int(dr.w*0.12),
                             dr.y + int(2*z) + bob,
                             int(dr.w*0.76), int(dr.h*0.32))
        pygame.draw.rect(screen, flash(self.color), head_r,
                         border_radius=int(10*z))

        # 머리카락
        hair_r = pygame.Rect(head_r.x + int(3*z), head_r.y + int(2*z),
                             head_r.w - int(6*z), int(head_r.h*0.38))
        pygame.draw.rect(screen, self.trim_color, hair_r,
                         border_radius=int(6*z))

        # 안경
        self._draw_glasses(screen, head_r, bob, z)

        # 팔
        self._draw_arms(screen, dr, bob, z, flash)

        # 스킬 빔
        if self.skill_timer > 6:
            self._draw_skill_beam(screen, dr, bob, z)

    # ── 렌더링 서브 메서드 ──────────────────────────────────────
    def _draw_shadow(self, screen, dr):
        sh = pygame.Surface((dr.w - int(8), 9), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 85), sh.get_rect())
        screen.blit(sh, (dr.x + 4, dr.y + dr.h - 3))

    def _draw_legs(self, screen, dr, bob, z, flash):
        lc = flash(self.trim_color)
        fc = flash(self.dark_color)
        leg_top = dr.y + int(dr.h * 0.73) + bob
        swing = int(math.sin(self.walk_t) * 7 * z) \
                if self.on_ground and abs(self.vel.x) > 0.5 else 0

        lw, lh = int(13*z), int(dr.h * 0.22)
        fw, fh = int(16*z), int(7*z)

        for side, sw in ((-1, -swing), (1, swing)):
            lx = dr.x + (int(dr.w*0.12) if side == -1 else int(dr.w*0.55))
            pygame.draw.rect(screen, lc,
                             (lx, leg_top + sw, lw, lh), border_radius=int(4*z))
            pygame.draw.rect(screen, fc,
                             (lx - int(2*z), leg_top + sw + lh, fw, fh),
                             border_radius=int(3*z))

    def _draw_arms(self, screen, dr, bob, z, flash):
        ac  = flash(self.color)
        arm_y = dr.y + int(dr.h * 0.30) + bob + int(4*z)

        if self.attack_timer > 0:
            prog  = 1.0 - self.attack_timer / self.ATK_FRAMES
            swing = int(math.sin(prog * math.pi) * 14 * z)
            ax    = dr.x + dr.w if self.facing == 1 else dr.x - int(20*z)
            ay    = arm_y - swing
            aw, ah = int(20*z), int(17*z)
            pygame.draw.rect(screen, ac, (ax, ay, aw, ah),
                             border_radius=int(5*z))
            if self.HIT_START <= self.attack_timer <= self.HIT_END:
                gr = int(38*z)
                gs = pygame.Surface((gr, gr), pygame.SRCALPHA)
                pygame.draw.circle(gs, (*self.glow_color, 130),
                                   (gr//2, gr//2), gr//2)
                screen.blit(gs, (ax + aw//2 - gr//2, ay + ah//2 - gr//2))
        else:
            # 대기 팔
            if self.facing == 1:
                pygame.draw.rect(screen, ac,
                                 (dr.x + dr.w - int(3*z), arm_y + int(2*z),
                                  int(12*z), int(14*z)),
                                 border_radius=int(4*z))
            else:
                pygame.draw.rect(screen, ac,
                                 (dr.x - int(9*z), arm_y + int(2*z),
                                  int(12*z), int(14*z)),
                                 border_radius=int(4*z))

    def _draw_glasses(self, screen, head_r, bob, z):
        ex = head_r.x + (int(head_r.w*0.62) if self.facing == 1
                         else int(head_r.w*0.22))
        ey = head_r.y + int(head_r.h * 0.42)
        lw, lh = int(13*z), int(10*z)
        pygame.draw.rect(screen, (210, 235, 255),
                         (ex - lw//2, ey - lh//2, lw, lh),
                         border_radius=int(3*z))
        pygame.draw.rect(screen, (90, 100, 130),
                         (ex - lw//2, ey - lh//2, lw, lh),
                         max(1, int(1*z)), border_radius=int(3*z))
        pygame.draw.circle(screen, (15, 15, 35),
                           (ex + self.facing, ey), max(1, int(3*z)))
        pygame.draw.circle(screen, (255, 255, 255),
                           (ex - 1, ey - int(2*z)), max(1, int(1*z)))

    def _draw_skill_aura(self, screen, dr, bob, z):
        t = self.skill_timer / 30.0
        r = int((55 + math.sin(self.bob_t * 4) * 7) * z)
        a = int(90 * t)
        sf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(sf, (*self.glow_color, a), (r, r), r)
        pygame.draw.circle(sf, (*self.glow_color, a//2), (r, r), r, int(3*z))
        screen.blit(sf, (dr.centerx - r, dr.centery - r + bob))

    def _draw_skill_beam(self, screen, dr, bob, z):
        t    = self.skill_timer / 30.0
        bl   = int(120 * z)
        bw   = max(int(4*z), int(16 * t * z))
        alp  = int(230 * t)
        bx   = dr.right - int(6*z) if self.facing == 1 else dr.left - bl + int(6*z)
        by   = dr.centery + bob - bw//2
        bs   = pygame.Surface((bl, bw + int(14*z)), pygame.SRCALPHA)
        pygame.draw.rect(bs, (*self.glow_color, alp),
                         (0, int(7*z), bl, bw), border_radius=int(5*z))
        pygame.draw.rect(bs, (*self.glow_color, alp//3),
                         (0, int(2*z), bl, bw + int(10*z)),
                         border_radius=int(7*z))
        pygame.draw.rect(bs, (255,255,255, int(alp*0.65)),
                         (0, int(7*z)+bw//2-int(2*z), bl, int(4*z)),
                         border_radius=int(5*z))
        screen.blit(bs, (bx, by - int(7*z)))

    def _draw_respawn_ghost(self, screen):
        t   = self.respawn_timer / 100.0
        a   = int(180 * t)
        x   = 38 if self.player_id == 1 else screen.get_width() - 148
        sf  = pygame.Surface((110, 36), pygame.SRCALPHA)
        sf.fill((0, 0, 0, 100))
        pygame.draw.rect(sf, (*self.glow_color, a), sf.get_rect(), 2,
                         border_radius=6)
        fnt = pygame.font.SysFont("Arial", 15, bold=True)
        secs = self.respawn_timer // 20 + 1
        txt = fnt.render(f"{self.name}  ✦{secs}", True, self.glow_color)
        sf.blit(txt, (8, 10))
        screen.blit(sf, (x, 55))
